#!/usr/bin/env python3
import argparse

from avxsim.measurement_csv import (
    convert_measurement_csv_to_npz,
    load_column_map_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert measured CSV rows to calibration_samples.npz"
    )
    p.add_argument("--input-csv", required=True, help="Input measurement CSV")
    p.add_argument("--output-npz", required=True, help="Output calibration_samples.npz")
    p.add_argument(
        "--column-map-json",
        default=None,
        help="Optional JSON map: canonical_key -> CSV column name",
    )
    p.add_argument(
        "--delimiter",
        default=",",
        help="CSV delimiter (default: ,)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    column_map = (
        load_column_map_json(args.column_map_json)
        if args.column_map_json is not None
        else None
    )
    samples = convert_measurement_csv_to_npz(
        csv_path=args.input_csv,
        out_npz=args.output_npz,
        column_map=column_map,
        delimiter=args.delimiter,
    )
    print("Measurement CSV conversion completed.")
    print(f"  samples: {samples['observed_gain'].shape[0]}")
    print(f"  output: {args.output_npz}")


if __name__ == "__main__":
    main()

