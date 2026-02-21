#!/usr/bin/env python3
import argparse
from pathlib import Path
from typing import Any, Dict, Optional

from avxsim.adc_pack_builder import build_measured_pack_from_adc_npz


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build one measured pack from ADC NPZ directory"
    )
    p.add_argument("--input-root", required=True, help="Directory containing ADC NPZ files")
    p.add_argument("--input-glob", default="*.npz", help="Glob pattern under input-root")
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--max-files", type=int, default=None)
    p.add_argument("--stride", type=int, default=1)
    p.add_argument("--output-pack-root", required=True)
    p.add_argument("--scenario-id", required=True)
    p.add_argument("--adc-key", default="adc")
    p.add_argument("--adc-order", default="sctr", help="Permutation of s,c,t,r")
    p.add_argument("--reference-index", type=int, default=0)
    p.add_argument("--nfft-range", type=int, default=None)
    p.add_argument("--nfft-doppler", type=int, default=None)
    p.add_argument("--nfft-angle", type=int, default=None)
    p.add_argument("--range-window", default="hann")
    p.add_argument("--doppler-window", default="hann")
    p.add_argument("--angle-window", default="hann")
    p.add_argument("--range-bin-limit", type=int, default=None)
    p.add_argument(
        "--path-power-fit-json",
        default=None,
        help="Optional fit JSON for measured-pack RD/RA proxy weighting",
    )
    p.add_argument("--fit-proxy-max-range-exp", type=float, default=None)
    p.add_argument("--fit-proxy-max-azimuth-power", type=float, default=None)
    p.add_argument("--fit-proxy-min-weight", type=float, default=None)
    p.add_argument("--fit-proxy-max-weight", type=float, default=None)
    return p.parse_args()


def _collect_files(input_root: str, pattern: str, recursive: bool) -> list:
    root = Path(input_root)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"input-root must be existing directory: {input_root}")
    files = sorted(root.rglob(pattern) if recursive else root.glob(pattern))
    return [str(p) for p in files if p.is_file()]


def main() -> None:
    args = parse_args()
    if int(args.stride) <= 0:
        raise ValueError("--stride must be positive")

    files = _collect_files(args.input_root, args.input_glob, recursive=bool(args.recursive))
    files = files[:: int(args.stride)]
    if args.max_files is not None:
        files = files[: int(args.max_files)]
    if len(files) == 0:
        raise ValueError("no ADC NPZ files found")

    fit_proxy_policy = _build_fit_proxy_policy(args)

    summary = build_measured_pack_from_adc_npz(
        adc_npz_files=files,
        output_pack_root=args.output_pack_root,
        scenario_id=args.scenario_id,
        adc_order=args.adc_order,
        adc_key=args.adc_key,
        reference_index=int(args.reference_index),
        nfft_range=args.nfft_range,
        nfft_doppler=args.nfft_doppler,
        nfft_angle=args.nfft_angle,
        range_window=args.range_window,
        doppler_window=args.doppler_window,
        angle_window=args.angle_window,
        range_bin_limit=args.range_bin_limit,
        path_power_fit_json=args.path_power_fit_json,
        fit_proxy_policy=fit_proxy_policy,
    )

    print("ADC pack build completed.")
    print(f"  scenario_id: {summary['scenario_id']}")
    print(f"  adc_files: {len(files)}")
    print(f"  candidate_count: {summary['candidate_count']}")
    print(f"  path_power_fit_json: {summary.get('path_power_fit_json')}")
    print(f"  fit_proxy_policy: {summary.get('fit_proxy_policy')}")
    print(f"  output_pack_root: {summary['output_pack_root']}")
    print(f"  replay_manifest_json: {summary['replay_manifest_json']}")


def _build_fit_proxy_policy(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    policy: Dict[str, Any] = {}
    if args.fit_proxy_max_range_exp is not None:
        policy["max_range_power_exponent"] = float(args.fit_proxy_max_range_exp)
    if args.fit_proxy_max_azimuth_power is not None:
        policy["max_azimuth_power"] = float(args.fit_proxy_max_azimuth_power)
    if args.fit_proxy_min_weight is not None:
        policy["min_weight"] = float(args.fit_proxy_min_weight)
    if args.fit_proxy_max_weight is not None:
        policy["max_weight"] = float(args.fit_proxy_max_weight)
    return policy if policy else None


if __name__ == "__main__":
    main()
