#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import numpy as np

from avxsim.replay_manifest_builder import (
    DEFAULT_CANDIDATE_GLOBS,
    build_replay_manifest_case,
    build_replay_manifest_payload,
    discover_candidate_npz_paths,
    save_replay_manifest_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate mock measured scenario packs for end-to-end replay execution"
    )
    p.add_argument("--output-root", required=True)
    p.add_argument(
        "--include-failing-pack",
        action="store_true",
        help="Add one pack with an intentionally failing candidate",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Random seed for reproducible synthetic variations",
    )
    return p.parse_args()


def _gaussian2d(shape, c0, c1, s0, s1, amp):
    y = np.arange(shape[0], dtype=np.float64)[:, None]
    x = np.arange(shape[1], dtype=np.float64)[None, :]
    z = np.exp(-0.5 * (((y - c0) / s0) ** 2 + ((x - c1) / s1) ** 2))
    return amp * z


def _write_est(path: Path, rd: np.ndarray, ra: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, fx_dop_win=rd, fx_ang=ra)


def _write_profile(path: Path, scenario_id: str, reference_npz: Path, motion_enabled: bool) -> None:
    payload = {
        "version": 1,
        "scenario_id": scenario_id,
        "created_utc": "2026-02-21T00:00:00+00:00",
        "global_jones_matrix": [
            {"re": 1.0, "im": 0.0},
            {"re": 0.0, "im": 0.0},
            {"re": 0.0, "im": 0.0},
            {"re": 1.0, "im": 0.0},
        ],
        "parity_thresholds": {
            "rd_peak_doppler_bin_abs_error_max": 2.0,
            "rd_peak_range_bin_abs_error_max": 2.0,
            "rd_peak_power_db_abs_error_max": 5.0,
            "rd_centroid_doppler_bin_abs_error_max": 2.0,
            "rd_centroid_range_bin_abs_error_max": 2.0,
            "rd_spread_doppler_rel_error_max": 0.5,
            "rd_spread_range_rel_error_max": 0.5,
            "rd_shape_nmse_max": 0.3,
            "ra_peak_angle_bin_abs_error_max": 2.0,
            "ra_peak_range_bin_abs_error_max": 2.0,
            "ra_peak_power_db_abs_error_max": 5.0,
            "ra_centroid_angle_bin_abs_error_max": 2.0,
            "ra_centroid_range_bin_abs_error_max": 2.0,
            "ra_spread_angle_rel_error_max": 0.5,
            "ra_spread_range_rel_error_max": 0.5,
            "ra_shape_nmse_max": 0.3,
        },
        "reference_estimation_npz": str(reference_npz),
        "motion_compensation_defaults": {
            "enabled": bool(motion_enabled),
            "fd_hz": 1100.0 if motion_enabled else None,
            "chirp_interval_s": 6e-5 if motion_enabled else None,
            "reference_tx": 0 if motion_enabled else None,
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_lock_policy(path: Path, require_motion_enabled: bool = True) -> None:
    payload = {
        "min_pass_rate": 1.0,
        "max_case_fail_count": 0,
        "require_motion_defaults_enabled": bool(require_motion_enabled),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_manifest(pack_root: Path, scenario_id: str, profile_json: Path) -> None:
    candidates = discover_candidate_npz_paths(
        pack_root=str(pack_root),
        candidate_globs=DEFAULT_CANDIDATE_GLOBS,
        exclude_globs=None,
    )
    case = build_replay_manifest_case(
        pack_root=str(pack_root),
        scenario_id=scenario_id,
        profile_json=str(profile_json),
        candidate_paths=[str(x) for x in candidates],
        reference_estimation_npz=None,
        include_sidecar_metadata=False,
        candidate_name_mode="stem",
    )
    save_replay_manifest_json(
        str(pack_root / "replay_manifest.json"),
        build_replay_manifest_payload([case]),
    )


def _create_pack(
    pack_root: Path,
    scenario_id: str,
    rng: np.random.Generator,
    include_bad: bool,
    motion_enabled: bool,
) -> None:
    pack_root.mkdir(parents=True, exist_ok=True)

    rd_ref = _gaussian2d((96, 128), 40.0, 62.0, 6.5, 8.0, 10.0)
    ra_ref = _gaussian2d((96, 128), 54.0, 61.0, 7.0, 6.0, 8.0)

    ref_npz = pack_root / "reference_estimation.npz"
    _write_est(ref_npz, rd_ref, ra_ref)

    profile_json = pack_root / "scenario_profile.json"
    _write_profile(profile_json, scenario_id=scenario_id, reference_npz=ref_npz, motion_enabled=motion_enabled)

    cdir = pack_root / "candidates"
    shift_a = int(rng.integers(0, 2))
    shift_b = int(rng.integers(0, 2))
    good_a = np.roll(rd_ref * 1.01, shift=shift_a, axis=0)
    good_b = np.roll(ra_ref * 0.99, shift=shift_b, axis=1)
    _write_est(cdir / "cand_good_1.npz", good_a, good_b)

    good2_a = np.roll(rd_ref * 0.995, shift=1, axis=1)
    good2_b = np.roll(ra_ref * 1.005, shift=1, axis=0)
    _write_est(cdir / "cand_good_2.npz", good2_a, good2_b)

    if include_bad:
        bad_a = np.roll(rd_ref, shift=14, axis=0)
        bad_b = np.roll(ra_ref, shift=-13, axis=0)
        _write_est(cdir / "cand_bad_1.npz", bad_a, bad_b)

    _write_lock_policy(pack_root / "lock_policy.json", require_motion_enabled=True)
    _build_manifest(pack_root, scenario_id=scenario_id, profile_json=profile_json)


def main() -> None:
    args = parse_args()
    root = Path(args.output_root)
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"output-root already exists and is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(int(args.seed))

    pack_static = root / "pack_static_v1"
    _create_pack(
        pack_root=pack_static,
        scenario_id="static_mock_v1",
        rng=rng,
        include_bad=False,
        motion_enabled=True,
    )

    pack_dynamic = root / "pack_dynamic_v1"
    _create_pack(
        pack_root=pack_dynamic,
        scenario_id="dynamic_mock_v1",
        rng=rng,
        include_bad=bool(args.include_failing_pack),
        motion_enabled=True,
    )

    print("Mock measured packs generated.")
    print(f"  output_root: {root}")
    print(f"  packs: 2")
    print(f"  include_failing_pack: {bool(args.include_failing_pack)}")
    print(f"  next: build plan using scripts/build_measured_replay_plan.py")


if __name__ == "__main__":
    main()
