#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from avxsim.xiangyu_path_power import (
    build_path_power_samples_from_xiangyu_sequence,
    save_path_power_rows_csv,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build path_power_samples.csv from Xiangyu text_labels + ADC frames"
    )
    p.add_argument("--adc-root", required=True, help="Directory containing ADC frames (.mat or .npz)")
    p.add_argument("--labels-root", required=True, help="Directory containing Xiangyu text_labels CSV files")
    p.add_argument("--output-csv", required=True)
    p.add_argument("--output-meta-json", default=None)

    p.add_argument("--scenario-id", default=None)
    p.add_argument("--adc-type", choices=["mat", "npz"], default="mat")
    p.add_argument("--adc-glob", default=None)
    p.add_argument("--labels-glob", default="*.csv")
    p.add_argument("--adc-key", default="adc")
    p.add_argument("--adc-order", default="scrt")
    p.add_argument("--mat-variable", default=None)

    p.add_argument("--max-frames", type=int, default=None)
    p.add_argument("--stride", type=int, default=1)
    p.add_argument("--min-py-m", type=float, default=0.0)
    p.add_argument("--distance-min-m", type=float, default=0.0)
    p.add_argument("--distance-max-m", type=float, default=100.0)
    p.add_argument("--range-max-m", type=float, default=30.0)

    p.add_argument("--nfft-range", type=int, default=None)
    p.add_argument("--nfft-doppler", type=int, default=None)
    p.add_argument("--nfft-angle", type=int, default=None)
    p.add_argument("--range-window", default="hann")
    p.add_argument("--doppler-window", default="hann")
    p.add_argument("--angle-window", default="hann")
    p.add_argument("--range-bin-limit", type=int, default=None)
    p.add_argument("--bin-search-radius", type=int, default=1)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_path_power_samples_from_xiangyu_sequence(
        adc_root_dir=args.adc_root,
        labels_root_dir=args.labels_root,
        scenario_id=args.scenario_id,
        adc_type=args.adc_type,
        adc_glob=args.adc_glob,
        labels_glob=args.labels_glob,
        adc_key=args.adc_key,
        adc_order=args.adc_order,
        mat_variable=args.mat_variable,
        max_frames=args.max_frames,
        stride=args.stride,
        min_py_m=args.min_py_m,
        distance_limits_m=(args.distance_min_m, args.distance_max_m),
        range_max_m=args.range_max_m,
        nfft_range=args.nfft_range,
        nfft_doppler=args.nfft_doppler,
        nfft_angle=args.nfft_angle,
        range_window=args.range_window,
        doppler_window=args.doppler_window,
        angle_window=args.angle_window,
        range_bin_limit=args.range_bin_limit,
        bin_search_radius=args.bin_search_radius,
    )

    rows = payload["rows"]
    meta = payload["metadata"]
    save_path_power_rows_csv(args.output_csv, rows)

    meta_json = Path(args.output_meta_json) if args.output_meta_json else None
    if meta_json is not None:
        meta_json.parent.mkdir(parents=True, exist_ok=True)
        meta_json.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("Xiangyu label->path-power CSV build completed.")
    print(f"  output_csv: {args.output_csv}")
    print(f"  selected_rows: {meta['selected_row_count']}")
    print(f"  matched_frames: {meta['matched_frame_count']}")
    print(f"  processed_frames: {meta['processed_frame_count']}")
    if meta_json is not None:
        print(f"  output_meta_json: {meta_json}")


if __name__ == "__main__":
    main()
