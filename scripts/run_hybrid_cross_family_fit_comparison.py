#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from avxsim.parity import compare_hybrid_estimation_npz


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run cross-family comparison using Hybrid ingest outputs with and without path-power fit. "
            "Reference is case-A baseline; report compares case-B baseline vs tuned."
        )
    )
    p.add_argument("--case-a-id", default="case_a")
    p.add_argument("--case-a-frames-root", required=True)
    p.add_argument("--case-a-radar-json", required=True)
    p.add_argument("--case-b-id", default="case_b")
    p.add_argument("--case-b-frames-root", required=True)
    p.add_argument("--case-b-radar-json", required=True)

    p.add_argument("--path-power-fit-json", required=True)
    p.add_argument("--path-power-apply-mode", choices=["shape_only", "replace"], default="shape_only")

    p.add_argument("--frame-start", type=int, required=True)
    p.add_argument("--frame-end", type=int, required=True)
    p.add_argument("--camera-fov-deg", type=float, required=True)
    p.add_argument("--mode", choices=["reflection", "scattering"], required=True)
    p.add_argument("--file-ext", default=".npy")

    p.add_argument("--fc-hz", type=float, default=77e9)
    p.add_argument("--slope-hz-per-s", type=float, default=20e12)
    p.add_argument("--fs-hz", type=float, default=20e6)
    p.add_argument("--samples-per-chirp", type=int, default=4096)
    p.add_argument("--amplitude-threshold", type=float, default=0.0)
    p.add_argument("--distance-min-m", type=float, default=0.0)
    p.add_argument("--distance-max-m", type=float, default=100.0)
    p.add_argument("--top-k-per-chirp", type=int, default=None)

    p.add_argument("--estimation-nfft", type=int, default=144)
    p.add_argument("--estimation-range-bin-length", type=int, default=10)
    p.add_argument("--estimation-doppler-window", default="hann")
    p.add_argument("--thresholds-json", default=None)

    p.add_argument("--run-case-a-tuned", action="store_true")
    p.add_argument("--output-root", required=True)
    p.add_argument("--output-summary-json", default=None)
    return p.parse_args()


def _run(cmd: List[str], cwd: Path, env: Mapping[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), env=dict(env), capture_output=True, text=True, check=False)


def _load_thresholds(path: Optional[str]) -> Optional[Dict[str, float]]:
    if path is None:
        return None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("thresholds-json must be object")
    return {str(k): float(v) for k, v in payload.items()}


def _ingest_cmd(args: argparse.Namespace, frames_root: str, radar_json: str, output_dir: str, fit_json: Optional[str]) -> List[str]:
    cmd = [
        "python3",
        "scripts/run_hybrid_ingest_to_adc.py",
        "--frames-root",
        str(frames_root),
        "--radar-json",
        str(radar_json),
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
        "--run-hybrid-estimation",
        "--estimation-nfft",
        str(args.estimation_nfft),
        "--estimation-range-bin-length",
        str(args.estimation_range_bin_length),
        "--estimation-doppler-window",
        str(args.estimation_doppler_window),
        "--output-dir",
        str(output_dir),
    ]
    if args.top_k_per_chirp is not None:
        cmd += ["--top-k-per-chirp", str(args.top_k_per_chirp)]
    if fit_json is not None:
        cmd += [
            "--path-power-fit-json",
            str(fit_json),
            "--path-power-apply-mode",
            str(args.path_power_apply_mode),
        ]
    return cmd


def _metric_delta(before: Mapping[str, float], after: Mapping[str, float]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for key in sorted(set(before.keys()) & set(after.keys())):
        b = float(before[key])
        a = float(after[key])
        out[str(key)] = {
            "before": b,
            "after": a,
            "delta": a - b,
            "improved": bool(a < b),
        }
    return out


def _group_summary(metric_delta: Mapping[str, Mapping[str, float]], prefix: str) -> Dict[str, Any]:
    vals = [v for k, v in metric_delta.items() if str(k).startswith(prefix)]
    if len(vals) == 0:
        return {
            "count": 0,
            "improved_count": 0,
            "improved_ratio": 0.0,
            "mean_delta": 0.0,
        }
    improved_count = sum(1 for v in vals if bool(v.get("improved", False)))
    mean_delta = sum(float(v.get("delta", 0.0)) for v in vals) / float(len(vals))
    return {
        "count": int(len(vals)),
        "improved_count": int(improved_count),
        "improved_ratio": float(improved_count) / float(len(vals)),
        "mean_delta": float(mean_delta),
    }


def main() -> None:
    args = parse_args()
    if int(args.frame_end) < int(args.frame_start):
        raise ValueError("frame-end must be >= frame-start")

    repo_root = Path(__file__).resolve().parents[1]
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    paths = {
        "a_baseline": output_root / f"{args.case_a_id}_baseline",
        "b_baseline": output_root / f"{args.case_b_id}_baseline",
        "b_tuned": output_root / f"{args.case_b_id}_tuned",
    }
    if args.run_case_a_tuned:
        paths["a_tuned"] = output_root / f"{args.case_a_id}_tuned"

    cmds: Dict[str, List[str]] = {
        "a_baseline": _ingest_cmd(args, args.case_a_frames_root, args.case_a_radar_json, str(paths["a_baseline"]), None),
        "b_baseline": _ingest_cmd(args, args.case_b_frames_root, args.case_b_radar_json, str(paths["b_baseline"]), None),
        "b_tuned": _ingest_cmd(args, args.case_b_frames_root, args.case_b_radar_json, str(paths["b_tuned"]), args.path_power_fit_json),
    }
    if args.run_case_a_tuned:
        cmds["a_tuned"] = _ingest_cmd(args, args.case_a_frames_root, args.case_a_radar_json, str(paths["a_tuned"]), args.path_power_fit_json)

    run_logs = {}
    for key in ["a_baseline", "b_baseline", "b_tuned"] + (["a_tuned"] if args.run_case_a_tuned else []):
        proc = _run(cmds[key], cwd=repo_root, env=env)
        run_logs[key] = {
            "returncode": int(proc.returncode),
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "command": cmds[key],
        }
        if proc.returncode != 0:
            raise RuntimeError(f"ingest failed for {key}:\n{proc.stdout}\n{proc.stderr}")

    thresholds = _load_thresholds(args.thresholds_json)
    ref_npz = str(paths["a_baseline"] / "hybrid_estimation.npz")
    b_base_npz = str(paths["b_baseline"] / "hybrid_estimation.npz")
    b_tuned_npz = str(paths["b_tuned"] / "hybrid_estimation.npz")

    b_base_report = compare_hybrid_estimation_npz(ref_npz, b_base_npz, thresholds=thresholds)
    b_tuned_report = compare_hybrid_estimation_npz(ref_npz, b_tuned_npz, thresholds=thresholds)

    a_tuned_report = None
    if args.run_case_a_tuned:
        a_tuned_npz = str(paths["a_tuned"] / "hybrid_estimation.npz")
        a_tuned_report = compare_hybrid_estimation_npz(ref_npz, a_tuned_npz, thresholds=thresholds)

    delta = _metric_delta(
        before=b_base_report.get("metrics", {}),
        after=b_tuned_report.get("metrics", {}),
    )

    summary = {
        "version": 1,
        "case_a_id": str(args.case_a_id),
        "case_b_id": str(args.case_b_id),
        "reference_npz": ref_npz,
        "path_power_fit_json": str(args.path_power_fit_json),
        "selection": {
            "mode": str(args.mode),
            "path_power_apply_mode": str(args.path_power_apply_mode),
            "frame_start": int(args.frame_start),
            "frame_end": int(args.frame_end),
            "camera_fov_deg": float(args.camera_fov_deg),
        },
        "outputs": {k: str(v) for k, v in paths.items()},
        "run_logs": run_logs,
        "comparisons": {
            "b_baseline_vs_a_baseline": b_base_report,
            "b_tuned_vs_a_baseline": b_tuned_report,
            "a_tuned_vs_a_baseline": a_tuned_report,
        },
        "cross_family_improvement": {
            "metric_delta": delta,
            "ra_summary": _group_summary(delta, prefix="ra_"),
            "rd_summary": _group_summary(delta, prefix="rd_"),
        },
    }

    out_json = (
        output_root / "hybrid_cross_family_fit_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json)
    )
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Hybrid cross-family fit comparison completed.")
    print(f"  case_a: {args.case_a_id}")
    print(f"  case_b: {args.case_b_id}")
    print(f"  b_baseline_pass: {b_base_report['pass']}")
    print(f"  b_tuned_pass: {b_tuned_report['pass']}")
    print(f"  ra_improved_ratio: {summary['cross_family_improvement']['ra_summary']['improved_ratio']:.3f}")
    print(f"  rd_improved_ratio: {summary['cross_family_improvement']['rd_summary']['improved_ratio']:.3f}")
    print(f"  output_summary_json: {out_json}")


if __name__ == "__main__":
    main()
