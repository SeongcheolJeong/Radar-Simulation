#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import numpy as np

from avxsim.path_power_tuning import (
    build_path_power_samples_from_csv,
    fit_path_power_parameters,
    load_column_map_json,
    save_path_power_fit_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run path-power parameter fitting batch across multiple CSV cases and models, "
            "and emit per-case fit JSONs with an aggregated summary."
        )
    )
    p.add_argument(
        "--csv-case",
        action="append",
        required=True,
        help="Repeatable label=path form for path-power sample CSV",
    )
    p.add_argument(
        "--model",
        action="append",
        default=None,
        choices=["reflection", "scattering"],
        help="Repeatable model list. Default: reflection and scattering",
    )
    p.add_argument("--batch-id", default="path_power_fit_batch")
    p.add_argument("--output-root", required=True)
    p.add_argument("--output-summary-json", default=None)

    p.add_argument("--column-map-json", default=None)
    p.add_argument("--delimiter", default=",")

    p.add_argument("--p-t-dbm", type=float, default=0.0)
    p.add_argument("--fc-hz", type=float, default=77e9)
    p.add_argument("--pixel-width", type=int, default=1)
    p.add_argument("--pixel-height", type=int, default=1)

    p.add_argument("--range-power-grid", default="2.5,3.0,3.5,4.0,4.5,5.0")
    p.add_argument("--elevation-power-grid", default="0.5,1.0,1.5,2.0,2.5,3.0")
    p.add_argument("--azimuth-mix-grid", default="0.0,0.2,0.4,0.6,0.8,1.0")
    p.add_argument("--azimuth-power-grid", default="1.0,2.0,3.0,4.0")
    p.add_argument("--top-k", type=int, default=10)
    return p.parse_args()


def _parse_label_path(text: str) -> Tuple[str, str]:
    s = str(text)
    if "=" not in s:
        raise ValueError("--csv-case must be label=path")
    label, path = s.split("=", 1)
    label = label.strip()
    path = path.strip()
    if label == "" or path == "":
        raise ValueError("--csv-case label/path must be non-empty")
    return label, path


def _parse_grid(text: str) -> List[float]:
    vals = [x.strip() for x in str(text).split(",")]
    out = [float(x) for x in vals if x != ""]
    if len(out) == 0:
        raise ValueError("grid must contain at least one value")
    return out


def _jsonify(v: Any) -> Any:
    if isinstance(v, dict):
        return {str(k): _jsonify(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonify(x) for x in v]
    if isinstance(v, np.floating):
        return float(v)
    if isinstance(v, np.integer):
        return int(v)
    return v


def _collect_param_stats(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    vals: Dict[str, List[float]] = {}
    for row in rows:
        params = row.get("best_params", {})
        if not isinstance(params, Mapping):
            continue
        for k, v in params.items():
            vals.setdefault(str(k), []).append(float(v))

    for key, arr0 in vals.items():
        arr = np.asarray(arr0, dtype=np.float64)
        out[key] = {
            "count": int(arr.size),
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
        }
    return out


def main() -> None:
    args = parse_args()
    models = args.model if args.model else ["reflection", "scattering"]
    cases = [_parse_label_path(x) for x in args.csv_case]

    cmap: Dict[str, str] = {}
    if args.column_map_json is not None:
        cmap = load_column_map_json(args.column_map_json)

    grid_common = {
        "range_power_exponent": _parse_grid(args.range_power_grid),
    }
    grid_scattering = {
        "elevation_power": _parse_grid(args.elevation_power_grid),
        "azimuth_mix": _parse_grid(args.azimuth_mix_grid),
        "azimuth_power": _parse_grid(args.azimuth_power_grid),
    }

    output_root = Path(args.output_root)
    fits_dir = output_root / "fits"
    fits_dir.mkdir(parents=True, exist_ok=True)

    run_rows = []
    for label, csv_path in cases:
        samples = build_path_power_samples_from_csv(
            csv_path=csv_path,
            column_map=cmap if cmap else None,
            delimiter=args.delimiter,
        )
        for model in models:
            grid = dict(grid_common)
            if model == "scattering":
                grid.update(grid_scattering)

            fit = fit_path_power_parameters(
                range_m=samples["range_m"],
                observed_amp=samples["observed_amp"],
                model=model,
                az_rad=samples["az_rad"],
                el_rad=samples["el_rad"],
                p_t_dbm=float(args.p_t_dbm),
                fc_hz=float(args.fc_hz),
                pixel_width=int(args.pixel_width),
                pixel_height=int(args.pixel_height),
                grid=grid,
                top_k=int(args.top_k),
            )

            fit_json = fits_dir / f"{label}_{model}.json"
            payload = {
                "version": 1,
                "batch_id": str(args.batch_id),
                "case_label": str(label),
                "input_csv": str(csv_path),
                "model": str(model),
                "fit": fit,
                "grid": grid,
                "column_map": cmap,
            }
            save_path_power_fit_json(str(fit_json), payload)

            row = {
                "case_label": str(label),
                "input_csv": str(csv_path),
                "model": str(model),
                "sample_count": int(fit["sample_count"]),
                "searched_candidates": int(fit["searched_candidates"]),
                "best_rmse_log": float(fit["best_metrics"]["rmse_log"]),
                "best_mae_log": float(fit["best_metrics"]["mae_log"]),
                "best_params": dict(fit["best_params"]),
                "fit_json": str(fit_json),
            }
            run_rows.append(row)

    by_model: Dict[str, Any] = {}
    for model in models:
        subset = [x for x in run_rows if str(x["model"]) == model]
        ranked = sorted(subset, key=lambda x: float(x["best_rmse_log"]))
        by_model[model] = {
            "count": len(subset),
            "ranked_by_rmse_log": ranked,
            "best_case": ranked[0] if ranked else None,
            "param_stats": _collect_param_stats(ranked),
        }

    summary = {
        "version": 1,
        "batch_id": str(args.batch_id),
        "models": list(models),
        "cases": [{"label": label, "csv": path} for label, path in cases],
        "run_count": len(run_rows),
        "fits_dir": str(fits_dir),
        "runs": run_rows,
        "by_model": by_model,
    }

    out_summary = (
        output_root / "path_power_fit_batch_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json)
    )
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    out_summary.write_text(json.dumps(_jsonify(summary), indent=2), encoding="utf-8")

    print("Path-power fit batch completed.")
    print(f"  batch_id: {args.batch_id}")
    print(f"  cases: {len(cases)}")
    print(f"  models: {','.join(models)}")
    print(f"  run_count: {len(run_rows)}")
    print(f"  fits_dir: {fits_dir}")
    print(f"  summary_json: {out_summary}")


if __name__ == "__main__":
    main()
