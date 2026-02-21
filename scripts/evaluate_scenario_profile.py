#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

from avxsim.parity import compare_hybrid_estimation_npz
from avxsim.scenario_profile import load_scenario_profile_json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate candidate estimation using scenario profile")
    p.add_argument("--profile-json", required=True)
    p.add_argument("--candidate-estimation-npz", required=True)
    p.add_argument(
        "--reference-estimation-npz",
        default=None,
        help="Optional override for profile reference",
    )
    p.add_argument("--output-json", default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    profile = load_scenario_profile_json(args.profile_json)
    reference = args.reference_estimation_npz
    if reference is None:
        reference = profile.get("reference_estimation_npz")
    if reference is None:
        raise ValueError("reference estimation npz is required (via profile or --reference-estimation-npz)")

    report = compare_hybrid_estimation_npz(
        reference_npz=str(reference),
        candidate_npz=str(args.candidate_estimation_npz),
        thresholds=profile["parity_thresholds"],
    )
    result = {
        "scenario_id": profile.get("scenario_id"),
        "reference_estimation_npz": str(reference),
        "candidate_estimation_npz": str(args.candidate_estimation_npz),
        "pass": bool(report["pass"]),
        "failures": report["failures"],
        "metrics": report["metrics"],
    }
    print(f"scenario_id: {result['scenario_id']}")
    print(f"parity pass: {result['pass']}")
    print(f"failure_count: {len(result['failures'])}")

    if args.output_json is not None:
        Path(args.output_json).write_text(json.dumps(result, indent=2), encoding="utf-8")
    sys.exit(0 if result["pass"] else 2)


if __name__ == "__main__":
    main()

