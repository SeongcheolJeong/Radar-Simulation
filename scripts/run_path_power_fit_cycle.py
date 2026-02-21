#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from avxsim.constants import C0
from avxsim.parity import compare_hybrid_estimation_npz


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run baseline->samples->fit->tuned ingest cycle and summarize path-power fit effect"
    )
    p.add_argument("--frames-root", required=True)
    p.add_argument("--radar-json", required=True)
    p.add_argument("--frame-start", type=int, required=True)
    p.add_argument("--frame-end", type=int, required=True)
    p.add_argument("--camera-fov-deg", type=float, required=True)
    p.add_argument("--mode", choices=["reflection", "scattering"], required=True)
    p.add_argument("--file-ext", default=".exr")

    p.add_argument("--fc-hz", type=float, default=77e9)
    p.add_argument("--slope-hz-per-s", type=float, default=20e12)
    p.add_argument("--fs-hz", type=float, default=20e6)
    p.add_argument("--samples-per-chirp", type=int, default=4096)
    p.add_argument("--amplitude-threshold", type=float, default=0.0)
    p.add_argument("--distance-min-m", type=float, default=0.0)
    p.add_argument("--distance-max-m", type=float, default=100.0)
    p.add_argument("--top-k-per-chirp", type=int, default=None)

    p.add_argument("--run-hybrid-estimation", action="store_true")
    p.add_argument("--estimation-nfft", type=int, default=144)
    p.add_argument("--estimation-range-bin-length", type=int, default=10)
    p.add_argument("--estimation-doppler-window", default="hann")

    p.add_argument("--samples-max-chirps", type=int, default=None)
    p.add_argument("--samples-max-paths-per-chirp", type=int, default=None)
    p.add_argument("--samples-min-observed-amp", type=float, default=0.0)
    p.add_argument("--samples-sort-by-amp-desc", action="store_true")

    p.add_argument("--fit-model", choices=["reflection", "scattering"], default=None)
    p.add_argument("--fit-p-t-dbm", type=float, default=0.0)
    p.add_argument("--fit-pixel-width", type=int, default=1)
    p.add_argument("--fit-pixel-height", type=int, default=1)
    p.add_argument("--fit-range-power-grid", default="2.5,3.0,3.5,4.0,4.5,5.0")
    p.add_argument("--fit-elevation-power-grid", default="0.5,1.0,1.5,2.0,2.5,3.0")
    p.add_argument("--fit-azimuth-mix-grid", default="0.0,0.2,0.4,0.6,0.8,1.0")
    p.add_argument("--fit-azimuth-power-grid", default="1.0,2.0,3.0,4.0")
    p.add_argument("--fit-top-k", type=int, default=10)

    p.add_argument("--path-power-apply-mode", choices=["shape_only", "replace"], default="shape_only")
    p.add_argument("--reference-estimation-npz", default=None)
    p.add_argument("--thresholds-json", default=None)

    p.add_argument("--work-root", required=True)
    p.add_argument("--scenario-id", default="path_power_cycle")
    p.add_argument("--output-summary-json", default=None)
    return p.parse_args()


def _run(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def _load_thresholds(path: Optional[str]) -> Optional[Dict[str, float]]:
    if path is None:
        return None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("thresholds-json must be a JSON object")
    return {str(k): float(v) for k, v in payload.items()}


def _load_range_amp(path_list_json: Path) -> Tuple[np.ndarray, np.ndarray]:
    payload = json.loads(path_list_json.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("path_list.json must be list")
    ranges = []
    amps = []
    for chirp_paths in payload:
        if not isinstance(chirp_paths, list):
            continue
        for p in chirp_paths:
            if not isinstance(p, dict):
                continue
            delay_s = float(p.get("delay_s", 0.0))
            amp_obj = p.get("amp_complex", {})
            if not isinstance(amp_obj, dict):
                continue
            amp = abs(complex(float(amp_obj.get("re", 0.0)), float(amp_obj.get("im", 0.0))))
            if delay_s > 0 and amp > 0:
                ranges.append((delay_s * C0) / 2.0)
                amps.append(amp)
    if len(ranges) == 0:
        raise ValueError(f"no valid range/amp rows in {path_list_json}")
    return np.asarray(ranges, dtype=np.float64), np.asarray(amps, dtype=np.float64)


def _log_slope_stats(range_m: np.ndarray, amp: np.ndarray) -> Dict[str, float]:
    r = np.asarray(range_m, dtype=np.float64).reshape(-1)
    a = np.asarray(amp, dtype=np.float64).reshape(-1)
    if r.size != a.size or r.size < 2:
        raise ValueError("need at least two range/amp rows")
    eps = np.finfo(np.float64).tiny
    x = np.log(np.maximum(r, eps))
    y = np.log(np.maximum(a, eps))
    xm = float(np.mean(x))
    ym = float(np.mean(y))
    varx = float(np.mean((x - xm) ** 2))
    if varx <= 0:
        raise ValueError("range has zero variance in log domain")
    cov = float(np.mean((x - xm) * (y - ym)))
    slope = cov / varx
    intercept = ym - slope * xm
    corr = cov / (np.sqrt(varx * float(np.mean((y - ym) ** 2))) + 1e-12)
    return {
        "count": int(r.size),
        "log_slope": float(slope),
        "log_intercept": float(intercept),
        "log_corrcoef": float(corr),
        "range_min_m": float(np.min(r)),
        "range_max_m": float(np.max(r)),
        "amp_min": float(np.min(a)),
        "amp_max": float(np.max(a)),
    }


def main() -> None:
    args = parse_args()
    if int(args.frame_end) < int(args.frame_start):
        raise ValueError("--frame-end must be >= --frame-start")

    repo_root = Path(__file__).resolve().parents[1]
    work_root = Path(args.work_root)
    work_root.mkdir(parents=True, exist_ok=True)

    baseline_dir = work_root / "baseline_ingest"
    tuned_dir = work_root / "tuned_ingest"
    samples_csv = work_root / "path_power_samples.csv"
    fit_json = work_root / f"path_power_fit_{str(args.mode)}.json"
    summary_json = (
        work_root / "path_power_cycle_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json)
    )

    base_cmd = [
        "python3",
        "scripts/run_hybrid_ingest_to_adc.py",
        "--frames-root",
        str(args.frames_root),
        "--radar-json",
        str(args.radar_json),
        "--frame-start",
        str(args.frame_start),
        "--frame-end",
        str(args.frame_end),
        "--camera-fov-deg",
        str(args.camera_fov_deg),
        "--mode",
        str(args.mode),
        "--file-ext",
        str(args.file_ext),
        "--fc-hz",
        str(args.fc_hz),
        "--slope-hz-per-s",
        str(args.slope_hz_per_s),
        "--fs-hz",
        str(args.fs_hz),
        "--samples-per-chirp",
        str(args.samples_per_chirp),
        "--amplitude-threshold",
        str(args.amplitude_threshold),
        "--distance-min-m",
        str(args.distance_min_m),
        "--distance-max-m",
        str(args.distance_max_m),
        "--path-power-apply-mode",
        str(args.path_power_apply_mode),
    ]
    if args.top_k_per_chirp is not None:
        base_cmd += ["--top-k-per-chirp", str(args.top_k_per_chirp)]
    if args.run_hybrid_estimation:
        base_cmd += [
            "--run-hybrid-estimation",
            "--estimation-nfft",
            str(args.estimation_nfft),
            "--estimation-range-bin-length",
            str(args.estimation_range_bin_length),
            "--estimation-doppler-window",
            str(args.estimation_doppler_window),
        ]

    cmd_baseline = base_cmd + ["--output-dir", str(baseline_dir)]
    proc_baseline = _run(cmd_baseline, cwd=repo_root)
    if proc_baseline.returncode != 0:
        raise RuntimeError(
            "baseline ingest failed:\n" + proc_baseline.stdout + "\n" + proc_baseline.stderr
        )

    cmd_samples = [
        "python3",
        "scripts/build_path_power_samples_from_path_list.py",
        "--input-path-list-json",
        str(baseline_dir / "path_list.json"),
        "--output-csv",
        str(samples_csv),
        "--scenario-id",
        str(args.scenario_id),
        "--min-observed-amp",
        str(args.samples_min_observed_amp),
    ]
    if args.samples_max_chirps is not None:
        cmd_samples += ["--max-chirps", str(args.samples_max_chirps)]
    if args.samples_max_paths_per_chirp is not None:
        cmd_samples += ["--max-paths-per-chirp", str(args.samples_max_paths_per_chirp)]
    if args.samples_sort_by_amp_desc:
        cmd_samples.append("--sort-by-amp-desc")
    proc_samples = _run(cmd_samples, cwd=repo_root)
    if proc_samples.returncode != 0:
        raise RuntimeError(
            "path-power sample build failed:\n" + proc_samples.stdout + "\n" + proc_samples.stderr
        )

    fit_model = str(args.mode) if args.fit_model is None else str(args.fit_model)
    cmd_fit = [
        "python3",
        "scripts/fit_path_power_model_from_csv.py",
        "--input-csv",
        str(samples_csv),
        "--model",
        fit_model,
        "--output-json",
        str(fit_json),
        "--p-t-dbm",
        str(args.fit_p_t_dbm),
        "--fc-hz",
        str(args.fc_hz),
        "--pixel-width",
        str(args.fit_pixel_width),
        "--pixel-height",
        str(args.fit_pixel_height),
        "--range-power-grid",
        str(args.fit_range_power_grid),
        "--elevation-power-grid",
        str(args.fit_elevation_power_grid),
        "--azimuth-mix-grid",
        str(args.fit_azimuth_mix_grid),
        "--azimuth-power-grid",
        str(args.fit_azimuth_power_grid),
        "--top-k",
        str(args.fit_top_k),
    ]
    proc_fit = _run(cmd_fit, cwd=repo_root)
    if proc_fit.returncode != 0:
        raise RuntimeError(
            "path-power fit failed:\n" + proc_fit.stdout + "\n" + proc_fit.stderr
        )

    cmd_tuned = base_cmd + [
        "--path-power-fit-json",
        str(fit_json),
        "--output-dir",
        str(tuned_dir),
    ]
    proc_tuned = _run(cmd_tuned, cwd=repo_root)
    if proc_tuned.returncode != 0:
        raise RuntimeError(
            "tuned ingest failed:\n" + proc_tuned.stdout + "\n" + proc_tuned.stderr
        )

    r_base, a_base = _load_range_amp(baseline_dir / "path_list.json")
    r_tuned, a_tuned = _load_range_amp(tuned_dir / "path_list.json")
    slope_base = _log_slope_stats(r_base, a_base)
    slope_tuned = _log_slope_stats(r_tuned, a_tuned)

    parity: Dict[str, Any] = {}
    if args.run_hybrid_estimation:
        baseline_est = baseline_dir / "hybrid_estimation.npz"
        tuned_est = tuned_dir / "hybrid_estimation.npz"
        if not baseline_est.exists() or not tuned_est.exists():
            raise RuntimeError("expected hybrid_estimation.npz from run-hybrid-estimation")
        ref_est = (
            str(args.reference_estimation_npz)
            if args.reference_estimation_npz is not None
            else str(baseline_est)
        )
        thresholds = _load_thresholds(args.thresholds_json)
        parity["reference_estimation_npz"] = str(ref_est)
        parity["baseline_vs_reference"] = compare_hybrid_estimation_npz(
            reference_npz=str(ref_est),
            candidate_npz=str(baseline_est),
            thresholds=thresholds,
        )
        parity["tuned_vs_reference"] = compare_hybrid_estimation_npz(
            reference_npz=str(ref_est),
            candidate_npz=str(tuned_est),
            thresholds=thresholds,
        )

    fit_payload = json.loads(fit_json.read_text(encoding="utf-8"))
    summary = {
        "version": 1,
        "scenario_id": str(args.scenario_id),
        "mode": str(args.mode),
        "work_root": str(work_root),
        "baseline_output_dir": str(baseline_dir),
        "tuned_output_dir": str(tuned_dir),
        "samples_csv": str(samples_csv),
        "fit_json": str(fit_json),
        "fit": fit_payload.get("fit", fit_payload),
        "path_amplitude_vs_range": {
            "baseline": slope_base,
            "tuned": slope_tuned,
            "delta_log_slope": float(slope_tuned["log_slope"]) - float(slope_base["log_slope"]),
        },
        "parity": parity,
        "commands": {
            "baseline_ingest": cmd_baseline,
            "build_samples": cmd_samples,
            "fit": cmd_fit,
            "tuned_ingest": cmd_tuned,
        },
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Path-power fit cycle completed.")
    print(f"  scenario_id: {args.scenario_id}")
    print(f"  mode: {args.mode}")
    print(f"  samples_csv: {samples_csv}")
    print(f"  fit_json: {fit_json}")
    print(f"  baseline_log_slope: {slope_base['log_slope']:.6f}")
    print(f"  tuned_log_slope: {slope_tuned['log_slope']:.6f}")
    print(f"  delta_log_slope: {summary['path_amplitude_vs_range']['delta_log_slope']:.6f}")
    if args.run_hybrid_estimation:
        tvr = summary["parity"]["tuned_vs_reference"]
        print(f"  tuned_vs_reference_pass: {tvr['pass']}")
    print(f"  summary_json: {summary_json}")


if __name__ == "__main__":
    main()
