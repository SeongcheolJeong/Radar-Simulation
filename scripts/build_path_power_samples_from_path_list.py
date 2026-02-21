#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

import numpy as np

from avxsim.constants import C0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build path-power sample CSV from path_list.json"
    )
    p.add_argument("--input-path-list-json", required=True)
    p.add_argument("--output-csv", required=True)
    p.add_argument("--scenario-id", default="scenario_from_path_list")
    p.add_argument("--max-chirps", type=int, default=None)
    p.add_argument("--max-paths-per-chirp", type=int, default=None)
    p.add_argument("--min-observed-amp", type=float, default=0.0)
    p.add_argument("--sort-by-amp-desc", action="store_true")
    return p.parse_args()


def _safe_complex_amp(item: dict) -> complex:
    c = item.get("amp_complex", None)
    if not isinstance(c, dict):
        raise ValueError("path item missing amp_complex object")
    return complex(float(c.get("re", 0.0)), float(c.get("im", 0.0)))


def _safe_unit_direction(item: dict):
    u = item.get("unit_direction", None)
    if not isinstance(u, list) or len(u) != 3:
        raise ValueError("path item missing unit_direction length-3")
    ux, uy, uz = float(u[0]), float(u[1]), float(u[2])
    return ux, uy, uz


def _row_from_path(path_item: dict, chirp_idx: int, path_idx: int, scenario_id: str):
    delay_s = float(path_item.get("delay_s", 0.0))
    if delay_s <= 0:
        raise ValueError("delay_s must be positive")
    ux, uy, uz = _safe_unit_direction(path_item)
    amp = _safe_complex_amp(path_item)
    observed_amp = abs(amp)
    range_m = (delay_s * C0) / 2.0
    az = float(np.arctan2(uy, ux))
    el = float(np.arcsin(np.clip(uz, -1.0, 1.0)))
    return {
        "scenario_id": str(scenario_id),
        "chirp_idx": int(chirp_idx),
        "path_idx": int(path_idx),
        "range_m": float(range_m),
        "az_rad": float(az),
        "el_rad": float(el),
        "observed_amp": float(observed_amp),
    }


def main() -> None:
    args = parse_args()
    payload = json.loads(Path(args.input_path_list_json).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("path_list.json must be list-of-chirps")

    chirps = payload if args.max_chirps is None else payload[: int(args.max_chirps)]
    rows = []
    for chirp_idx, chirp_paths in enumerate(chirps):
        if not isinstance(chirp_paths, list):
            raise ValueError("path_list chirp entry must be list")
        local = []
        for path_idx, p in enumerate(chirp_paths):
            if not isinstance(p, dict):
                raise ValueError("path item must be object")
            row = _row_from_path(
                path_item=p,
                chirp_idx=int(chirp_idx),
                path_idx=int(path_idx),
                scenario_id=str(args.scenario_id),
            )
            if float(row["observed_amp"]) >= float(args.min_observed_amp):
                local.append(row)
        if args.sort_by_amp_desc:
            local = sorted(local, key=lambda x: float(x["observed_amp"]), reverse=True)
        if args.max_paths_per_chirp is not None:
            local = local[: int(args.max_paths_per_chirp)]
        rows.extend(local)

    if len(rows) == 0:
        raise ValueError("no rows selected for output CSV")

    out_csv = Path(args.output_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    cols = ["scenario_id", "chirp_idx", "path_idx", "range_m", "az_rad", "el_rad", "observed_amp"]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in rows:
            w.writerow(row)

    print("Path-power sample CSV build completed.")
    print(f"  input_path_list_json: {args.input_path_list_json}")
    print(f"  output_csv: {args.output_csv}")
    print(f"  rows: {len(rows)}")
    print(f"  scenario_id: {args.scenario_id}")


if __name__ == "__main__":
    main()
