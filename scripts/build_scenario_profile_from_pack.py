#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import List, Optional

from avxsim.calibration import load_global_jones_matrix_json
from avxsim.parity import DEFAULT_PARITY_THRESHOLDS, compare_hybrid_estimation_npz
from avxsim.scenario_profile import (
    build_scenario_profile_payload,
    derive_parity_thresholds,
    save_scenario_profile_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Rebuild scenario_profile.json from pack candidates by deriving parity thresholds"
    )
    p.add_argument("--pack-root", required=True)
    p.add_argument("--case-index", type=int, default=0)
    p.add_argument("--reference-candidate-index", type=int, default=0)
    p.add_argument("--candidate-stride", type=int, default=1)
    p.add_argument("--max-candidates", type=int, default=None)
    p.add_argument("--threshold-quantile", type=float, default=1.0)
    p.add_argument("--threshold-margin", type=float, default=1.05)
    p.add_argument("--threshold-floor", choices=["defaults", "none"], default="none")
    p.add_argument(
        "--output-profile-json",
        default=None,
        help="Default: <pack-root>/scenario_profile.json",
    )
    p.add_argument(
        "--backup-original",
        action="store_true",
        help="When overwriting default profile path, write scenario_profile.default.json once",
    )
    return p.parse_args()


def _load_manifest_case(pack_root: Path, case_index: int) -> dict:
    manifest_json = pack_root / "replay_manifest.json"
    if not manifest_json.exists():
        raise FileNotFoundError(str(manifest_json))
    payload = json.loads(manifest_json.read_text(encoding="utf-8"))
    cases = payload.get("cases", None)
    if not isinstance(cases, list) or len(cases) == 0:
        raise ValueError("replay_manifest.json must contain non-empty 'cases'")
    i = int(case_index)
    if i < 0 or i >= len(cases):
        raise ValueError(f"case-index out of range: {i}")
    case = cases[i]
    if not isinstance(case, dict):
        raise ValueError("manifest case must be object")
    cands = case.get("candidates", None)
    if not isinstance(cands, list) or len(cands) == 0:
        raise ValueError("manifest case must contain non-empty 'candidates'")
    return case


def _collect_candidate_paths(case: dict, stride: int, max_candidates: Optional[int]) -> List[str]:
    if int(stride) <= 0:
        raise ValueError("--candidate-stride must be positive")
    paths = []
    for c in case["candidates"]:
        if not isinstance(c, dict) or "estimation_npz" not in c:
            raise ValueError("each candidate must include estimation_npz")
        paths.append(str(c["estimation_npz"]))
    paths = paths[:: int(stride)]
    if max_candidates is not None:
        if int(max_candidates) <= 0:
            raise ValueError("--max-candidates must be positive when set")
        paths = paths[: int(max_candidates)]
    if len(paths) == 0:
        raise ValueError("no candidate paths selected after stride/max-candidates")
    return paths


def main() -> None:
    args = parse_args()
    pack_root = Path(args.pack_root)
    if not pack_root.exists() or not pack_root.is_dir():
        raise ValueError(f"pack-root must be existing directory: {pack_root}")

    case = _load_manifest_case(pack_root, case_index=int(args.case_index))
    candidate_paths = _collect_candidate_paths(
        case=case,
        stride=int(args.candidate_stride),
        max_candidates=args.max_candidates,
    )

    ref_idx = int(args.reference_candidate_index)
    if ref_idx < 0 or ref_idx >= len(candidate_paths):
        raise ValueError("--reference-candidate-index out of selected candidate range")
    ref_npz = candidate_paths[ref_idx]

    metric_reports = []
    for p in candidate_paths:
        rep = compare_hybrid_estimation_npz(
            reference_npz=str(ref_npz),
            candidate_npz=str(p),
            thresholds=None,
        )
        metric_reports.append(rep["metrics"])

    floor = DEFAULT_PARITY_THRESHOLDS if args.threshold_floor == "defaults" else None
    thresholds = derive_parity_thresholds(
        metric_reports=metric_reports,
        quantile=float(args.threshold_quantile),
        margin=float(args.threshold_margin),
        floor_thresholds=floor,
    )

    default_profile_json = pack_root / "scenario_profile.json"
    output_profile_json = (
        default_profile_json
        if args.output_profile_json is None
        else Path(args.output_profile_json)
    )

    if not default_profile_json.exists():
        raise FileNotFoundError(
            "pack is missing scenario_profile.json required for global_jones/motion defaults"
        )
    base_profile = json.loads(default_profile_json.read_text(encoding="utf-8"))
    global_jones = load_global_jones_matrix_json(str(default_profile_json))

    if bool(args.backup_original) and output_profile_json.resolve() == default_profile_json.resolve():
        backup = pack_root / "scenario_profile.default.json"
        if not backup.exists():
            backup.write_text(default_profile_json.read_text(encoding="utf-8"), encoding="utf-8")

    payload = build_scenario_profile_payload(
        scenario_id=str(base_profile.get("scenario_id", case.get("scenario_id", "scenario_from_pack"))),
        global_jones_matrix=global_jones,
        parity_thresholds=thresholds,
        reference_estimation_npz=str(ref_npz),
        train_estimation_npz=[str(x) for x in candidate_paths],
        threshold_derivation={
            "method": "from_pack_candidates",
            "source_pack_root": str(pack_root),
            "case_index": int(args.case_index),
            "reference_candidate_index": int(ref_idx),
            "candidate_stride": int(args.candidate_stride),
            "max_candidates": None if args.max_candidates is None else int(args.max_candidates),
            "threshold_quantile": float(args.threshold_quantile),
            "threshold_margin": float(args.threshold_margin),
            "threshold_floor": str(args.threshold_floor),
            "train_count": int(len(candidate_paths)),
        },
        motion_compensation_defaults=base_profile.get(
            "motion_compensation_defaults",
            {
                "enabled": False,
                "fd_hz": None,
                "chirp_interval_s": None,
                "reference_tx": None,
            },
        ),
    )
    output_profile_json.parent.mkdir(parents=True, exist_ok=True)
    save_scenario_profile_json(str(output_profile_json), payload)

    print("Scenario profile rebuild from pack completed.")
    print(f"  pack_root: {pack_root}")
    print(f"  output_profile_json: {output_profile_json}")
    print(f"  selected_candidates: {len(candidate_paths)}")
    print(f"  reference_estimation_npz: {ref_npz}")
    print(f"  threshold_keys: {len(thresholds)}")
    print(f"  threshold_quantile: {args.threshold_quantile}")
    print(f"  threshold_margin: {args.threshold_margin}")
    print(f"  threshold_floor: {args.threshold_floor}")


if __name__ == "__main__":
    main()
