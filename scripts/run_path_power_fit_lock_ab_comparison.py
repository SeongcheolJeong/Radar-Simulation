#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Compare two locked path-power fit assets (RMSE-only vs cross-family) "
            "using the same Hybrid cross-family comparator setup."
        )
    )
    p.add_argument("--case-a-id", default="case_a")
    p.add_argument("--case-a-frames-root", required=True)
    p.add_argument("--case-a-radar-json", required=True)
    p.add_argument("--case-b-id", default="case_b")
    p.add_argument("--case-b-frames-root", required=True)
    p.add_argument("--case-b-radar-json", required=True)

    p.add_argument("--mode", choices=["reflection", "scattering"], required=True)
    p.add_argument("--rmse-fit-json", required=True)
    p.add_argument("--cross-family-fit-json", required=True)
    p.add_argument("--rmse-label", default="rmse_lock")
    p.add_argument("--cross-family-label", default="cross_family_lock")

    p.add_argument("--path-power-apply-mode", choices=["shape_only", "replace"], default="shape_only")

    p.add_argument("--frame-start", type=int, required=True)
    p.add_argument("--frame-end", type=int, required=True)
    p.add_argument("--camera-fov-deg", type=float, required=True)
    p.add_argument("--file-ext", default=".npy")
    p.add_argument("--amplitude-prefix", default="AmplitudeOutput")
    p.add_argument("--distance-prefix", default=None)
    p.add_argument("--distance-scale", type=float, default=None)

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

    p.add_argument("--output-root", required=True)
    p.add_argument("--output-summary-json", default=None)
    return p.parse_args()


def _run(cmd: List[str], cwd: Path, env: Mapping[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), env=dict(env), capture_output=True, text=True, check=False)


def _load_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json must be object: {path}")
    return payload


def _metric_delta(before: Mapping[str, float], after: Mapping[str, float]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for key in sorted(set(before.keys()) & set(after.keys())):
        b = float(before[key])
        a = float(after[key])
        d = a - b
        out[str(key)] = {
            "before": b,
            "after": a,
            "delta": d,
            "improved": bool(d < 0.0),
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


def _score_from_summary(run_summary: Mapping[str, Any]) -> float:
    cmp_report = run_summary.get("comparisons", {}).get("b_tuned_vs_a_baseline", {})
    pass_penalty = 0.0 if bool(cmp_report.get("pass", False)) else 1.0
    ra_mean = float(run_summary.get("cross_family_improvement", {}).get("ra_summary", {}).get("mean_delta", 0.0))
    rd_mean = float(run_summary.get("cross_family_improvement", {}).get("rd_summary", {}).get("mean_delta", 0.0))
    return (10.0 * pass_penalty) + (2.0 * ra_mean) + (1.0 * rd_mean)


def _build_comparator_cmd(args: argparse.Namespace, fit_json: str, output_root: Path, output_summary_json: Path) -> List[str]:
    cmd = [
        "python3",
        "scripts/run_hybrid_cross_family_fit_comparison.py",
        "--case-a-id",
        str(args.case_a_id),
        "--case-a-frames-root",
        str(args.case_a_frames_root),
        "--case-a-radar-json",
        str(args.case_a_radar_json),
        "--case-b-id",
        str(args.case_b_id),
        "--case-b-frames-root",
        str(args.case_b_frames_root),
        "--case-b-radar-json",
        str(args.case_b_radar_json),
        "--path-power-fit-json",
        str(fit_json),
        "--path-power-apply-mode",
        str(args.path_power_apply_mode),
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
        "--amplitude-prefix",
        str(args.amplitude_prefix),
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
        "--estimation-nfft",
        str(args.estimation_nfft),
        "--estimation-range-bin-length",
        str(args.estimation_range_bin_length),
        "--estimation-doppler-window",
        str(args.estimation_doppler_window),
        "--output-root",
        str(output_root),
        "--output-summary-json",
        str(output_summary_json),
    ]
    if args.top_k_per_chirp is not None:
        cmd += ["--top-k-per-chirp", str(args.top_k_per_chirp)]
    if args.distance_prefix is not None:
        cmd += ["--distance-prefix", str(args.distance_prefix)]
    if args.distance_scale is not None:
        cmd += ["--distance-scale", str(args.distance_scale)]
    if args.thresholds_json is not None:
        cmd += ["--thresholds-json", str(args.thresholds_json)]
    return cmd


def main() -> None:
    args = parse_args()
    if int(args.frame_end) < int(args.frame_start):
        raise ValueError("frame-end must be >= frame-start")

    repo_root = Path(__file__).resolve().parents[1]
    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    runs = [
        {
            "id": "rmse_lock",
            "label": str(args.rmse_label),
            "fit_json": str(args.rmse_fit_json),
        },
        {
            "id": "cross_family_lock",
            "label": str(args.cross_family_label),
            "fit_json": str(args.cross_family_fit_json),
        },
    ]

    run_outputs: Dict[str, Dict[str, Any]] = {}
    for run in runs:
        run_id = str(run["id"])
        cmp_out = out_root / run_id
        cmp_summary = cmp_out / "hybrid_cross_family_fit_summary.json"
        cmd = _build_comparator_cmd(
            args=args,
            fit_json=str(run["fit_json"]),
            output_root=cmp_out,
            output_summary_json=cmp_summary,
        )
        proc = _run(cmd, cwd=repo_root, env=env)
        if proc.returncode != 0:
            raise RuntimeError(
                f"comparator failed for {run_id}:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
            )
        payload = _load_json(str(cmp_summary))
        tuned = payload.get("comparisons", {}).get("b_tuned_vs_a_baseline", {})
        metrics = tuned.get("metrics", {})
        if not isinstance(metrics, Mapping):
            raise ValueError(f"invalid comparator output metrics: {cmp_summary}")
        score = _score_from_summary(payload)
        run_outputs[run_id] = {
            "id": run_id,
            "label": str(run["label"]),
            "fit_json": str(run["fit_json"]),
            "summary_json": str(cmp_summary),
            "b_tuned_pass": bool(tuned.get("pass", False)),
            "b_tuned_metrics": {str(k): float(v) for k, v in metrics.items()},
            "ra_mean_delta": float(payload.get("cross_family_improvement", {}).get("ra_summary", {}).get("mean_delta", 0.0)),
            "rd_mean_delta": float(payload.get("cross_family_improvement", {}).get("rd_summary", {}).get("mean_delta", 0.0)),
            "score": float(score),
        }

    rmse_metrics = run_outputs["rmse_lock"]["b_tuned_metrics"]
    cross_metrics = run_outputs["cross_family_lock"]["b_tuned_metrics"]
    ab_delta = _metric_delta(before=rmse_metrics, after=cross_metrics)

    rmse_score = float(run_outputs["rmse_lock"]["score"])
    cross_score = float(run_outputs["cross_family_lock"]["score"])
    score_tie = abs(rmse_score - cross_score) <= 1e-12
    winner_id = "cross_family_lock"
    winner_reason = "score_tie_prefers_cross_family"
    if rmse_score < cross_score:
        winner_id = "rmse_lock"
        winner_reason = "lower_score"
    elif cross_score < rmse_score:
        winner_id = "cross_family_lock"
        winner_reason = "lower_score"

    summary = {
        "version": 1,
        "mode": str(args.mode),
        "selection": {
            "case_a_id": str(args.case_a_id),
            "case_b_id": str(args.case_b_id),
            "frame_start": int(args.frame_start),
            "frame_end": int(args.frame_end),
            "camera_fov_deg": float(args.camera_fov_deg),
            "file_ext": str(args.file_ext),
            "amplitude_prefix": str(args.amplitude_prefix),
            "distance_prefix": None if args.distance_prefix is None else str(args.distance_prefix),
            "distance_scale": None if args.distance_scale is None else float(args.distance_scale),
            "path_power_apply_mode": str(args.path_power_apply_mode),
        },
        "runs": run_outputs,
        "ab_comparison": {
            "metric_delta_cross_minus_rmse": ab_delta,
            "ra_summary": _group_summary(ab_delta, prefix="ra_"),
            "rd_summary": _group_summary(ab_delta, prefix="rd_"),
            "score_tie": bool(score_tie),
            "winner_run_id": winner_id,
            "winner_label": str(run_outputs[winner_id]["label"]),
            "winner_reason": str(winner_reason),
            "cross_family_better": bool(winner_id == "cross_family_lock"),
        },
    }

    out_summary = (
        out_root / "path_power_fit_lock_ab_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json)
    )
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Path-power fit lock A/B comparison completed.")
    print(f"  mode: {args.mode}")
    print(f"  rmse_score: {run_outputs['rmse_lock']['score']:.6f}")
    print(f"  cross_family_score: {run_outputs['cross_family_lock']['score']:.6f}")
    print(f"  winner: {summary['ab_comparison']['winner_label']}")
    print(f"  output_summary_json: {out_summary}")


if __name__ == "__main__":
    main()
