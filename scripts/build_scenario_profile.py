#!/usr/bin/env python3
import argparse

import numpy as np

from avxsim.calibration import fit_global_jones_matrix, load_global_jones_matrix_json
from avxsim.parity import DEFAULT_PARITY_THRESHOLDS, compare_hybrid_estimation_npz
from avxsim.scenario_profile import (
    build_scenario_profile_payload,
    derive_parity_thresholds,
    save_scenario_profile_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build scenario profile (global Jones + parity thresholds)"
    )
    p.add_argument("--scenario-id", required=True)
    p.add_argument(
        "--samples-npz",
        default=None,
        help="Calibration samples NPZ to fit global Jones matrix",
    )
    p.add_argument(
        "--global-jones-json",
        default=None,
        help="Existing global Jones JSON (used when samples-npz is not provided)",
    )
    p.add_argument(
        "--ridge",
        type=float,
        default=0.0,
        help="Ridge regularization used only when fitting from samples",
    )
    p.add_argument(
        "--reference-estimation-npz",
        default=None,
        help="Reference hybrid_estimation.npz for threshold derivation",
    )
    p.add_argument(
        "--train-estimation-npz",
        action="append",
        default=[],
        help="Training candidate estimation NPZ (repeatable)",
    )
    p.add_argument("--threshold-quantile", type=float, default=0.95)
    p.add_argument("--threshold-margin", type=float, default=1.25)
    p.add_argument(
        "--threshold-floor",
        choices=["defaults", "none"],
        default="defaults",
        help="Apply DEFAULT_PARITY_THRESHOLDS as floor or not",
    )
    p.add_argument("--output-profile-json", required=True)
    return p.parse_args()


def _fit_or_load_global_jones(args: argparse.Namespace):
    if args.samples_npz is not None:
        with np.load(args.samples_npz, allow_pickle=False) as s:
            for key in ["tx_jones", "rx_jones", "observed_gain"]:
                if key not in s:
                    raise ValueError(f"samples-npz missing key: {key}")
            fit = fit_global_jones_matrix(
                tx_jones=s["tx_jones"],
                rx_jones=s["rx_jones"],
                observed_gain=s["observed_gain"],
                path_matrices=s["path_matrices"] if "path_matrices" in s else None,
                ridge=float(args.ridge),
            )
            return fit["global_jones_matrix"], fit["metrics"]
    if args.global_jones_json is not None:
        return load_global_jones_matrix_json(args.global_jones_json), None
    raise ValueError("one of --samples-npz or --global-jones-json is required")


def _derive_thresholds(args: argparse.Namespace):
    if args.reference_estimation_npz is None or len(args.train_estimation_npz) == 0:
        return dict(DEFAULT_PARITY_THRESHOLDS), None

    reports = []
    for cand in args.train_estimation_npz:
        rep = compare_hybrid_estimation_npz(
            reference_npz=args.reference_estimation_npz,
            candidate_npz=cand,
            thresholds=None,
        )
        reports.append(rep["metrics"])

    floor = DEFAULT_PARITY_THRESHOLDS if args.threshold_floor == "defaults" else None
    thresholds = derive_parity_thresholds(
        metric_reports=reports,
        quantile=float(args.threshold_quantile),
        margin=float(args.threshold_margin),
        floor_thresholds=floor,
    )
    derivation = {
        "reference_estimation_npz": str(args.reference_estimation_npz),
        "train_estimation_npz": [str(x) for x in args.train_estimation_npz],
        "threshold_quantile": float(args.threshold_quantile),
        "threshold_margin": float(args.threshold_margin),
        "threshold_floor": str(args.threshold_floor),
    }
    return thresholds, derivation


def main() -> None:
    args = parse_args()
    j_global, fit_metrics = _fit_or_load_global_jones(args)
    thresholds, derivation = _derive_thresholds(args)
    profile = build_scenario_profile_payload(
        scenario_id=args.scenario_id,
        global_jones_matrix=j_global,
        parity_thresholds=thresholds,
        reference_estimation_npz=args.reference_estimation_npz,
        fit_metrics=fit_metrics,
        train_estimation_npz=args.train_estimation_npz,
        threshold_derivation=derivation,
    )
    save_scenario_profile_json(args.output_profile_json, profile)

    print("Scenario profile build completed.")
    print(f"  scenario_id: {args.scenario_id}")
    print(f"  output: {args.output_profile_json}")
    print(f"  thresholds: {len(thresholds)}")
    print(f"  global_jones_source: {'samples' if args.samples_npz is not None else 'json'}")


if __name__ == "__main__":
    main()

