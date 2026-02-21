#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Rank path-power fit candidates using Hybrid cross-family comparator metrics."
        )
    )
    p.add_argument("--candidate-fit-json", action="append", default=None)
    p.add_argument("--experiment-summary-json", default=None)
    p.add_argument("--model", choices=["reflection", "scattering"], required=True)

    p.add_argument("--case-a-id", default="case_a")
    p.add_argument("--case-a-frames-root", required=True)
    p.add_argument("--case-a-radar-json", required=True)
    p.add_argument("--case-b-id", default="case_b")
    p.add_argument("--case-b-frames-root", required=True)
    p.add_argument("--case-b-radar-json", required=True)

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


def _load_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json must be object: {path}")
    return payload


def _collect_candidates_from_experiment(exp_json: str, model: str) -> List[str]:
    payload = _load_json(exp_json)
    experiments = payload.get("experiments", [])
    if not isinstance(experiments, list):
        raise ValueError("experiment summary missing experiments list")
    out: List[str] = []
    for exp in experiments:
        if not isinstance(exp, Mapping):
            continue
        fit_summary = exp.get("fit_summary", None)
        if not isinstance(fit_summary, Mapping):
            continue
        runs = fit_summary.get("runs", None)
        if not isinstance(runs, list):
            continue
        for run in runs:
            if not isinstance(run, Mapping):
                continue
            if str(run.get("model", "")).strip().lower() != str(model):
                continue
            p = str(run.get("fit_json", "")).strip()
            if p != "":
                out.append(p)
    dedup = []
    seen = set()
    for p in out:
        if p not in seen:
            seen.add(p)
            dedup.append(p)
    return dedup


def _run(cmd: Sequence[str], cwd: Path, env: Mapping[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), env=dict(env), capture_output=True, text=True, check=False)


def _score(row: Mapping[str, Any]) -> float:
    # Lower score is better: prioritize reducing RA mean delta, then RD mean delta.
    ra = float(row.get("ra_mean_delta", 0.0))
    rd = float(row.get("rd_mean_delta", 0.0))
    pass_penalty = 0.0 if bool(row.get("b_tuned_pass", False)) else 1.0
    return (10.0 * pass_penalty) + (2.0 * ra) + (1.0 * rd)


def main() -> None:
    args = parse_args()
    if int(args.frame_end) < int(args.frame_start):
        raise ValueError("frame-end must be >= frame-start")

    candidates = list(args.candidate_fit_json or [])
    if args.experiment_summary_json is not None:
        candidates.extend(_collect_candidates_from_experiment(args.experiment_summary_json, model=args.model))
    candidates = [str(Path(p)) for p in candidates]
    if len(candidates) == 0:
        raise ValueError("no candidate fit json paths were provided/discovered")

    # Keep only existing files and preserve order.
    uniq: List[str] = []
    seen = set()
    for p in candidates:
        if p in seen:
            continue
        if not Path(p).exists():
            continue
        seen.add(p)
        uniq.append(p)
    if len(uniq) == 0:
        raise ValueError("no existing candidate fit json files")

    repo_root = Path(__file__).resolve().parents[1]
    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    rows: List[Dict[str, Any]] = []
    for i, fit_json in enumerate(uniq):
        cand_out = out_root / f"candidate_{i:03d}"
        summary_json = cand_out / "hybrid_cross_family_fit_summary.json"
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
            str(args.model),
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
            str(cand_out),
            "--output-summary-json",
            str(summary_json),
        ]
        if args.top_k_per_chirp is not None:
            cmd += ["--top-k-per-chirp", str(args.top_k_per_chirp)]
        if args.distance_prefix is not None:
            cmd += ["--distance-prefix", str(args.distance_prefix)]
        if args.distance_scale is not None:
            cmd += ["--distance-scale", str(args.distance_scale)]
        if args.thresholds_json is not None:
            cmd += ["--thresholds-json", str(args.thresholds_json)]

        proc = _run(cmd, cwd=repo_root, env=env)
        if proc.returncode != 0:
            rows.append(
                {
                    "candidate_index": int(i),
                    "fit_json": str(fit_json),
                    "status": "error",
                    "returncode": int(proc.returncode),
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "summary_json": str(summary_json),
                }
            )
            continue

        report = _load_json(str(summary_json))
        ra = report.get("cross_family_improvement", {}).get("ra_summary", {})
        rd = report.get("cross_family_improvement", {}).get("rd_summary", {})
        row = {
            "candidate_index": int(i),
            "fit_json": str(fit_json),
            "status": "ok",
            "summary_json": str(summary_json),
            "b_baseline_pass": bool(report.get("comparisons", {}).get("b_baseline_vs_a_baseline", {}).get("pass", False)),
            "b_tuned_pass": bool(report.get("comparisons", {}).get("b_tuned_vs_a_baseline", {}).get("pass", False)),
            "ra_improved_ratio": float(ra.get("improved_ratio", 0.0)),
            "ra_mean_delta": float(ra.get("mean_delta", 0.0)),
            "rd_improved_ratio": float(rd.get("improved_ratio", 0.0)),
            "rd_mean_delta": float(rd.get("mean_delta", 0.0)),
        }
        row["score"] = float(_score(row))
        rows.append(row)

    ok_rows = [r for r in rows if r.get("status") == "ok"]
    ranked = sorted(ok_rows, key=lambda x: float(x.get("score", 1e18)))

    summary = {
        "version": 1,
        "model": str(args.model),
        "case_a_id": str(args.case_a_id),
        "case_b_id": str(args.case_b_id),
        "candidate_count": len(uniq),
        "evaluated_count": len(rows),
        "ok_count": len(ok_rows),
        "ranked": ranked,
        "all_rows": rows,
        "best": ranked[0] if len(ranked) > 0 else None,
    }

    out_summary = (
        out_root / "path_power_fit_cross_family_ranking_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json)
    )
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Path-power fit cross-family ranking completed.")
    print(f"  model: {args.model}")
    print(f"  candidate_count: {len(uniq)}")
    print(f"  ok_count: {len(ok_rows)}")
    if len(ranked) > 0:
        print(f"  best_fit_json: {ranked[0]['fit_json']}")
        print(f"  best_score: {ranked[0]['score']:.6f}")
    print(f"  output_summary_json: {out_summary}")


if __name__ == "__main__":
    main()
