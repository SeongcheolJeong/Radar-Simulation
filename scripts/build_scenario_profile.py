#!/usr/bin/env python3
import argparse

import numpy as np

from avxsim.calibration import fit_global_jones_matrix, load_global_jones_matrix_json
from avxsim.motion_tuning import (
    DEFAULT_MOTION_SCORE_WEIGHTS,
    load_motion_tuning_manifest_json,
    select_best_motion_tuning_candidate,
)
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
    p.add_argument(
        "--motion-default-enabled",
        action="store_true",
        help="Set motion compensation default enabled in scenario profile",
    )
    p.add_argument(
        "--motion-default-fd-hz",
        type=float,
        default=None,
        help="Optional default Doppler for motion compensation in scenario profile",
    )
    p.add_argument(
        "--motion-default-chirp-interval-s",
        type=float,
        default=None,
        help="Optional default chirp interval for motion compensation in scenario profile",
    )
    p.add_argument(
        "--motion-default-reference-tx",
        type=int,
        default=None,
        help="Optional default reference Tx index for motion compensation in scenario profile",
    )
    p.add_argument(
        "--motion-tuning-manifest-json",
        default=None,
        help="Optional JSON manifest listing candidate estimation NPZs and motion params",
    )
    p.add_argument(
        "--motion-score-weight",
        action="append",
        default=[],
        help="Optional weight override as key=value (e.g., ra_peak_angle_bin_abs_error=2.0)",
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


def _parse_motion_score_weights(items):
    weights = dict(DEFAULT_MOTION_SCORE_WEIGHTS)
    for raw in items:
        text = str(raw)
        if "=" not in text:
            raise ValueError(f"invalid --motion-score-weight: {raw}")
        key, value = text.split("=", 1)
        k = key.strip()
        if k == "":
            raise ValueError(f"invalid --motion-score-weight key: {raw}")
        weights[k] = float(value)
    return weights


def _resolve_motion_defaults(args: argparse.Namespace):
    defaults = {
        "enabled": bool(args.motion_default_enabled),
        "fd_hz": None if args.motion_default_fd_hz is None else float(args.motion_default_fd_hz),
        "chirp_interval_s": None
        if args.motion_default_chirp_interval_s is None
        else float(args.motion_default_chirp_interval_s),
        "reference_tx": None
        if args.motion_default_reference_tx is None
        else int(args.motion_default_reference_tx),
    }
    summary = None
    if args.motion_tuning_manifest_json is not None:
        if args.reference_estimation_npz is None:
            raise ValueError("--reference-estimation-npz is required with --motion-tuning-manifest-json")
        candidates = load_motion_tuning_manifest_json(args.motion_tuning_manifest_json)
        weights = _parse_motion_score_weights(args.motion_score_weight)
        best, ranked = select_best_motion_tuning_candidate(
            reference_estimation_npz=args.reference_estimation_npz,
            candidates=candidates,
            score_weights=weights,
        )
        defaults = dict(best["motion_compensation"])
        summary = {
            "manifest_json": str(args.motion_tuning_manifest_json),
            "score_weights": weights,
            "selected_name": best["name"],
            "selected_estimation_npz": best["estimation_npz"],
            "selected_score": float(best["score"]),
            "ranked": ranked,
        }
    return defaults, summary


def main() -> None:
    args = parse_args()
    j_global, fit_metrics = _fit_or_load_global_jones(args)
    thresholds, derivation = _derive_thresholds(args)
    motion_defaults, motion_summary = _resolve_motion_defaults(args)
    profile = build_scenario_profile_payload(
        scenario_id=args.scenario_id,
        global_jones_matrix=j_global,
        parity_thresholds=thresholds,
        reference_estimation_npz=args.reference_estimation_npz,
        fit_metrics=fit_metrics,
        train_estimation_npz=args.train_estimation_npz,
        threshold_derivation=derivation,
        motion_compensation_defaults=motion_defaults,
        motion_tuning_summary=motion_summary,
    )
    save_scenario_profile_json(args.output_profile_json, profile)

    print("Scenario profile build completed.")
    print(f"  scenario_id: {args.scenario_id}")
    print(f"  output: {args.output_profile_json}")
    print(f"  thresholds: {len(thresholds)}")
    print(f"  global_jones_source: {'samples' if args.samples_npz is not None else 'json'}")
    print(f"  motion_default_enabled: {motion_defaults['enabled']}")
    print(f"  motion_default_fd_hz: {motion_defaults['fd_hz']}")
    print(f"  motion_default_chirp_interval_s: {motion_defaults['chirp_interval_s']}")


if __name__ == "__main__":
    main()
