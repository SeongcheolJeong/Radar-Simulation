#!/usr/bin/env python3
import argparse
import glob
import json
from pathlib import Path

import numpy as np

from avxsim.adapters import adapt_records_by_chirp, load_records_by_chirp_json
from avxsim.antenna import FfdAntennaModel
from avxsim.calibration_samples import build_calibration_samples, save_calibration_samples_npz
from avxsim.types import RadarConfig


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build calibration samples npz from path_list.json + adc_cube.npz")
    p.add_argument("--path-list-json", required=True, help="Path list JSON output")
    p.add_argument("--adc-npz", required=True, help="ADC cube NPZ output")
    p.add_argument("--tx-ffd-glob", required=True, help="Glob for Tx .ffd files")
    p.add_argument("--rx-ffd-glob", required=True, help="Glob for Rx .ffd files")
    p.add_argument(
        "--ffd-field-format",
        choices=["auto", "real_imag", "mag_phase_deg"],
        default="auto",
    )
    p.add_argument(
        "--observed-mode",
        choices=["normalized", "raw"],
        default="normalized",
        help="normalized: divide by scalar path model; raw: direct matched-filter complex gain",
    )
    p.add_argument("--max-paths-per-chirp", type=int, default=1)
    p.add_argument("--min-path-amp", type=float, default=0.0)
    p.add_argument("--output-npz", required=True, help="Output calibration samples NPZ path")
    return p.parse_args()


def _resolve_glob(pattern: str):
    items = sorted(glob.glob(pattern))
    if not items:
        raise ValueError(f"no files matched pattern: {pattern}")
    return items


def _load_adc_and_metadata(path: str):
    with np.load(path, allow_pickle=False) as payload:
        if "adc" not in payload:
            raise ValueError("adc-npz missing key: adc")
        if "metadata_json" not in payload:
            raise ValueError("adc-npz missing key: metadata_json")
        adc = payload["adc"]
        meta = json.loads(str(payload["metadata_json"].tolist()))
    return adc, meta


def _radar_from_metadata(meta: dict) -> RadarConfig:
    required = ["fc_hz", "slope_hz_per_s", "fs_hz", "samples_per_chirp", "tx_schedule"]
    for key in required:
        if key not in meta:
            raise ValueError(f"metadata_json missing key: {key}")
    return RadarConfig(
        fc_hz=float(meta["fc_hz"]),
        slope_hz_per_s=float(meta["slope_hz_per_s"]),
        fs_hz=float(meta["fs_hz"]),
        samples_per_chirp=int(meta["samples_per_chirp"]),
        tx_schedule=[int(x) for x in meta["tx_schedule"]],
    )


def main() -> None:
    args = parse_args()
    tx_ffd_files = _resolve_glob(args.tx_ffd_glob)
    rx_ffd_files = _resolve_glob(args.rx_ffd_glob)
    adc, meta = _load_adc_and_metadata(args.adc_npz)
    radar = _radar_from_metadata(meta)

    tx_pos = np.asarray(meta.get("tx_pos_m", []), dtype=np.float64)
    rx_pos = np.asarray(meta.get("rx_pos_m", []), dtype=np.float64)
    if tx_pos.ndim != 2 or tx_pos.shape[1] != 3:
        raise ValueError("metadata_json.tx_pos_m must have shape (n_tx,3)")
    if rx_pos.ndim != 2 or rx_pos.shape[1] != 3:
        raise ValueError("metadata_json.rx_pos_m must have shape (n_rx,3)")

    records = load_records_by_chirp_json(args.path_list_json)
    paths_by_chirp = adapt_records_by_chirp(records_by_chirp=records, fc_hz=float(meta["fc_hz"]))
    ant = FfdAntennaModel.from_files(
        tx_ffd_files=tx_ffd_files,
        rx_ffd_files=rx_ffd_files,
        n_tx=int(tx_pos.shape[0]),
        n_rx=int(rx_pos.shape[0]),
        field_format=args.ffd_field_format,
    )
    samples = build_calibration_samples(
        paths_by_chirp=paths_by_chirp,
        adc=adc,
        radar=radar,
        tx_pos_m=tx_pos,
        rx_pos_m=rx_pos,
        antenna_model=ant,
        observed_mode=args.observed_mode,
        max_paths_per_chirp=int(args.max_paths_per_chirp),
        min_path_amp=float(args.min_path_amp),
    )

    metadata = {
        "source_path_list_json": str(Path(args.path_list_json)),
        "source_adc_npz": str(Path(args.adc_npz)),
        "observed_mode": str(args.observed_mode),
        "max_paths_per_chirp": int(args.max_paths_per_chirp),
        "min_path_amp": float(args.min_path_amp),
        "tx_ffd_files": [str(x) for x in tx_ffd_files],
        "rx_ffd_files": [str(x) for x in rx_ffd_files],
    }
    save_calibration_samples_npz(args.output_npz, samples, metadata=metadata)

    print("Calibration samples build completed.")
    print(f"  samples: {samples['observed_gain'].shape[0]}")
    print(f"  observed_mode: {args.observed_mode}")
    print(f"  output: {args.output_npz}")


if __name__ == "__main__":
    main()
