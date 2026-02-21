#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Select model-wise path-power fit JSONs from experiment matrix summary and "
            "emit locked/recommended fit artifacts."
        )
    )
    p.add_argument("--experiment-summary-json", required=True)
    p.add_argument("--model", action="append", default=None, choices=["reflection", "scattering"])
    p.add_argument(
        "--selection-strategy",
        choices=["largest_frame_then_rmse", "lowest_rmse"],
        default="largest_frame_then_rmse",
    )
    p.add_argument("--output-dir", required=True)
    p.add_argument("--output-summary-json", default=None)
    return p.parse_args()


def _load_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json must be object: {path}")
    return payload


def _collect_rows(exp_summary: Mapping[str, Any], model: str) -> List[Dict[str, Any]]:
    experiments = exp_summary.get("experiments", None)
    if not isinstance(experiments, list):
        raise ValueError("experiment summary missing experiments[]")

    rows: List[Dict[str, Any]] = []
    for exp_idx, exp in enumerate(experiments):
        if not isinstance(exp, Mapping):
            continue
        frame_count = int(exp.get("frame_count", 0))
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
            fit_json = str(run.get("fit_json", "")).strip()
            if fit_json == "":
                continue
            rows.append(
                {
                    "experiment_index": int(exp_idx),
                    "frame_count": int(frame_count),
                    "case_label": str(run.get("case_label", "")),
                    "model": str(model),
                    "best_rmse_log": float(run.get("best_rmse_log", 0.0)),
                    "best_mae_log": float(run.get("best_mae_log", 0.0)),
                    "sample_count": int(run.get("sample_count", 0)),
                    "fit_json": str(fit_json),
                    "source_run": dict(run),
                }
            )
    return rows


def _select_row(rows: List[Dict[str, Any]], strategy: str) -> Dict[str, Any]:
    if len(rows) == 0:
        raise ValueError("no candidate rows for selection")
    strategy_name = str(strategy)
    if strategy_name == "lowest_rmse":
        return sorted(rows, key=lambda x: float(x["best_rmse_log"]))[0]

    max_fc = max(int(r["frame_count"]) for r in rows)
    subset = [r for r in rows if int(r["frame_count"]) == int(max_fc)]
    if len(subset) == 0:
        subset = list(rows)
    return sorted(subset, key=lambda x: float(x["best_rmse_log"]))[0]


def _emit_selected_fit(
    selected_row: Mapping[str, Any],
    strategy: str,
    output_path: Path,
    experiment_summary_json: str,
) -> Dict[str, Any]:
    src_fit = _load_json(str(selected_row["fit_json"]))
    src_fit["selection"] = {
        "source_experiment_summary_json": str(experiment_summary_json),
        "selection_strategy": str(strategy),
        "selected_row": {
            "case_label": str(selected_row["case_label"]),
            "frame_count": int(selected_row["frame_count"]),
            "best_rmse_log": float(selected_row["best_rmse_log"]),
            "best_mae_log": float(selected_row["best_mae_log"]),
            "sample_count": int(selected_row["sample_count"]),
            "fit_json": str(selected_row["fit_json"]),
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(src_fit, indent=2), encoding="utf-8")
    return src_fit


def main() -> None:
    args = parse_args()
    exp_summary = _load_json(args.experiment_summary_json)

    models = args.model if args.model else ["reflection", "scattering"]
    strategy = str(args.selection_strategy)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    selected_models = []
    for model in models:
        rows = _collect_rows(exp_summary=exp_summary, model=model)
        selected = _select_row(rows, strategy=strategy)
        out_fit_json = out_dir / f"path_power_fit_{model}_selected.json"
        fit_payload = _emit_selected_fit(
            selected_row=selected,
            strategy=strategy,
            output_path=out_fit_json,
            experiment_summary_json=args.experiment_summary_json,
        )

        selected_models.append(
            {
                "model": str(model),
                "strategy": str(strategy),
                "candidate_count": len(rows),
                "selected": {
                    "case_label": str(selected["case_label"]),
                    "frame_count": int(selected["frame_count"]),
                    "best_rmse_log": float(selected["best_rmse_log"]),
                    "best_mae_log": float(selected["best_mae_log"]),
                    "sample_count": int(selected["sample_count"]),
                    "source_fit_json": str(selected["fit_json"]),
                    "output_fit_json": str(out_fit_json),
                },
                "selected_best_params": fit_payload.get("fit", {}).get("best_params", {}),
            }
        )

    summary = {
        "version": 1,
        "experiment_summary_json": str(args.experiment_summary_json),
        "selection_strategy": str(strategy),
        "models": selected_models,
    }

    out_summary = (
        out_dir / "path_power_fit_selection_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json)
    )
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Path-power fit selection completed.")
    print(f"  strategy: {strategy}")
    print(f"  models: {','.join(models)}")
    print(f"  output_dir: {out_dir}")
    print(f"  output_summary_json: {out_summary}")


if __name__ == "__main__":
    main()
