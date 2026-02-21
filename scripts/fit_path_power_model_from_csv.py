#!/usr/bin/env python3
import argparse
import json
from typing import Dict, List

from avxsim.path_power_tuning import (
    build_path_power_samples_from_csv,
    fit_path_power_parameters,
    load_column_map_json,
    save_path_power_fit_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fit reflection/scattering path-power parameters from measured CSV"
    )
    p.add_argument("--input-csv", required=True)
    p.add_argument("--model", choices=["reflection", "scattering"], required=True)
    p.add_argument("--output-json", required=True)
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


def _parse_grid(text: str) -> List[float]:
    items = [x.strip() for x in str(text).split(",")]
    out = [float(x) for x in items if x != ""]
    if len(out) == 0:
        raise ValueError("grid string must contain at least one numeric value")
    return out


def main() -> None:
    args = parse_args()
    cmap: Dict[str, str] = {}
    if args.column_map_json is not None:
        cmap = load_column_map_json(args.column_map_json)

    samples = build_path_power_samples_from_csv(
        csv_path=args.input_csv,
        column_map=cmap if cmap else None,
        delimiter=args.delimiter,
    )
    grid = {
        "range_power_exponent": _parse_grid(args.range_power_grid),
    }
    if args.model == "scattering":
        grid["elevation_power"] = _parse_grid(args.elevation_power_grid)
        grid["azimuth_mix"] = _parse_grid(args.azimuth_mix_grid)
        grid["azimuth_power"] = _parse_grid(args.azimuth_power_grid)

    fit = fit_path_power_parameters(
        range_m=samples["range_m"],
        observed_amp=samples["observed_amp"],
        model=args.model,
        az_rad=samples["az_rad"],
        el_rad=samples["el_rad"],
        p_t_dbm=float(args.p_t_dbm),
        fc_hz=float(args.fc_hz),
        pixel_width=int(args.pixel_width),
        pixel_height=int(args.pixel_height),
        grid=grid,
        top_k=int(args.top_k),
    )

    payload = {
        "version": 1,
        "input_csv": str(args.input_csv),
        "model": str(args.model),
        "fit": fit,
        "grid": grid,
        "column_map": cmap,
    }
    save_path_power_fit_json(args.output_json, payload)

    print("Path power model fit completed.")
    print(f"  model: {args.model}")
    print(f"  samples: {fit['sample_count']}")
    print(f"  searched_candidates: {fit['searched_candidates']}")
    print(f"  best_params: {json.dumps(fit['best_params'])}")
    print(f"  best_rmse_log: {fit['best_metrics']['rmse_log']:.6f}")
    print(f"  output_json: {args.output_json}")


if __name__ == "__main__":
    main()
