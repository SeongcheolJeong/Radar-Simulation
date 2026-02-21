#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple


PRESET_GRIDS: Dict[str, Dict[str, str]] = {
    "flat": {
        "range_power_grid": "0.5,1.0,1.5",
        "elevation_power_grid": "0.0,0.5,1.0",
        "azimuth_mix_grid": "0.0,0.5,1.0",
        "azimuth_power_grid": "0.0,1.0,2.0",
    },
    "balanced": {
        "range_power_grid": "1.0,1.5,2.0",
        "elevation_power_grid": "0.5,1.0,1.5",
        "azimuth_mix_grid": "0.2,0.5,0.8",
        "azimuth_power_grid": "1.0,2.0",
    },
    "steep": {
        "range_power_grid": "2.5,3.5,5.0",
        "elevation_power_grid": "1.5,2.0,2.5",
        "azimuth_mix_grid": "0.2,0.5,0.8",
        "azimuth_power_grid": "2.0,3.0,4.0",
    },
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run constrained refit loop (preset grids) and evaluate fit-lock search in drift mode."
        )
    )
    p.add_argument("--case", action="append", required=True, help="label=pack_root or label=pack_root::baseline_report")
    p.add_argument("--csv-case", action="append", required=True, help="label=path_power_samples_csv")
    p.add_argument(
        "--preset",
        action="append",
        choices=sorted(PRESET_GRIDS.keys()),
        default=None,
        help="Refit preset list. Default: flat,balanced,steep",
    )
    p.add_argument("--stop-on-adopt", action="store_true", help="Stop loop when adopt recommendation is achieved")
    p.add_argument("--baseline-mode", choices=["rerun", "provided"], default="rerun")
    p.add_argument("--allow-unlocked", action="store_true")
    p.add_argument("--output-root", required=True)
    p.add_argument("--output-summary-json", default=None)
    return p.parse_args()


def _run(cmd: Sequence[str], cwd: Path, env: Mapping[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), env=dict(env), capture_output=True, text=True, check=False)


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json must be object: {path}")
    return payload


def _status_rank(recommendation: str) -> int:
    r = str(recommendation)
    if r == "adopt_selected_fit_by_drift_objective":
        return 0
    if r == "exploratory_fit_candidate_selected_by_drift":
        return 1
    if r == "fallback_to_baseline_no_fit":
        return 2
    return 3


def _rank_key(row: Mapping[str, Any]) -> Tuple[float, float]:
    rec = str(row.get("selection_recommendation", ""))
    score = row.get("selected_aggregate_score", None)
    score_v = float(score) if isinstance(score, (int, float)) else 1e18
    return (float(_status_rank(rec)), float(score_v))


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    out_root = Path(args.output_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    presets = args.preset if args.preset else ["flat", "balanced", "steep"]
    rows: List[Dict[str, Any]] = []

    for pi, preset in enumerate(presets):
        grid = PRESET_GRIDS[str(preset)]
        preset_root = out_root / f"preset_{pi:02d}_{preset}"
        preset_root.mkdir(parents=True, exist_ok=True)

        fit_batch_summary_json = preset_root / "path_power_fit_batch_summary.json"
        cmd_fit = [
            "python3",
            "scripts/run_path_power_fit_batch.py",
            "--batch-id",
            f"constrained_refit_{preset}",
            "--output-root",
            str(preset_root / "fit_batch"),
            "--output-summary-json",
            str(fit_batch_summary_json),
            "--range-power-grid",
            str(grid["range_power_grid"]),
            "--elevation-power-grid",
            str(grid["elevation_power_grid"]),
            "--azimuth-mix-grid",
            str(grid["azimuth_mix_grid"]),
            "--azimuth-power-grid",
            str(grid["azimuth_power_grid"]),
        ]
        for c in args.csv_case:
            cmd_fit.extend(["--csv-case", str(c)])

        p_fit = _run(cmd_fit, cwd=repo_root, env=env)
        if p_fit.returncode != 0:
            rows.append(
                {
                    "preset": str(preset),
                    "fit_batch_ok": False,
                    "error": f"fit_batch_failed: {p_fit.stderr.strip()}",
                }
            )
            continue

        fit_batch_payload = _load_json(fit_batch_summary_json)
        runs = fit_batch_payload.get("runs", [])
        if not isinstance(runs, list) or len(runs) == 0:
            rows.append(
                {
                    "preset": str(preset),
                    "fit_batch_ok": False,
                    "error": "fit_batch_empty_runs",
                }
            )
            continue
        fit_jsons = []
        for r in runs:
            if not isinstance(r, Mapping):
                continue
            fp = str(r.get("fit_json", "")).strip()
            if fp != "":
                fit_jsons.append(fp)
        fit_jsons = sorted(set(fit_jsons))
        if len(fit_jsons) == 0:
            rows.append(
                {
                    "preset": str(preset),
                    "fit_batch_ok": False,
                    "error": "fit_batch_no_fit_json",
                }
            )
            continue

        search_summary_json = preset_root / "fit_lock_search_summary.json"
        cmd_search = [
            "python3",
            "scripts/run_measured_replay_fit_lock_search.py",
            "--baseline-mode",
            str(args.baseline_mode),
            "--objective-mode",
            "drift",
            "--output-root",
            str(preset_root / "search_run"),
            "--output-summary-json",
            str(search_summary_json),
        ]
        if args.allow_unlocked:
            cmd_search.append("--allow-unlocked")
        for c in args.case:
            cmd_search.extend(["--case", str(c)])
        for fit_json in fit_jsons:
            cmd_search.extend(["--fit-json", str(fit_json)])

        p_search = _run(cmd_search, cwd=repo_root, env=env)
        if p_search.returncode != 0:
            rows.append(
                {
                    "preset": str(preset),
                    "fit_batch_ok": True,
                    "fit_json_count": len(fit_jsons),
                    "search_ok": False,
                    "error": f"search_failed: {p_search.stderr.strip()}",
                    "fit_batch_summary_json": str(fit_batch_summary_json),
                }
            )
            continue

        search_payload = _load_json(search_summary_json)
        sel = search_payload.get("selection", {})
        if not isinstance(sel, Mapping):
            sel = {}
        selected_summary = sel.get("selected_fit_summary", {})
        if not isinstance(selected_summary, Mapping):
            selected_summary = {}
        row = {
            "preset": str(preset),
            "fit_batch_ok": True,
            "fit_batch_summary_json": str(fit_batch_summary_json),
            "fit_json_count": len(fit_jsons),
            "search_ok": True,
            "search_summary_json": str(search_summary_json),
            "selection_mode": str(sel.get("selection_mode", "")),
            "selection_recommendation": str(sel.get("recommendation", "")),
            "selected_fit_json": sel.get("selected_fit_json", None),
            "selected_aggregate_score": selected_summary.get("aggregate_score", None),
            "objective_effective": str(search_payload.get("objective_effective", "")),
            "short_circuit": bool(search_payload.get("short_circuit", False)),
        }
        rows.append(row)

        if args.stop_on_adopt and row["selection_recommendation"] == "adopt_selected_fit_by_drift_objective":
            break

    good_rows = [x for x in rows if bool(x.get("search_ok", False))]
    best_row = sorted(good_rows, key=_rank_key)[0] if len(good_rows) > 0 else None

    summary = {
        "version": 1,
        "baseline_mode": str(args.baseline_mode),
        "preset_count": int(len(presets)),
        "case_count": int(len(args.case)),
        "csv_case_count": int(len(args.csv_case)),
        "rows": rows,
        "best": best_row,
    }

    out_summary_json = (
        out_root / "constrained_refit_drift_search_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json).expanduser().resolve()
    )
    out_summary_json.parent.mkdir(parents=True, exist_ok=True)
    out_summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Constrained refit drift search completed.")
    print(f"  preset_count: {summary['preset_count']}")
    print(f"  rows: {len(rows)}")
    print(f"  best_preset: {None if best_row is None else best_row.get('preset')}")
    print(f"  output_summary_json: {out_summary_json}")


if __name__ == "__main__":
    main()
