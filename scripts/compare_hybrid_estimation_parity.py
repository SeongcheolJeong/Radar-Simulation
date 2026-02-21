#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

from avxsim.parity import compare_hybrid_estimation_npz


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare two Hybrid estimation npz files with parity metrics.")
    p.add_argument("--reference-npz", required=True, help="Reference hybrid_estimation.npz path")
    p.add_argument("--candidate-npz", required=True, help="Candidate hybrid_estimation.npz path")
    p.add_argument(
        "--thresholds-json",
        default=None,
        help="Optional JSON file path overriding threshold keys in DEFAULT_PARITY_THRESHOLDS",
    )
    p.add_argument(
        "--output-json",
        default=None,
        help="Optional output JSON report path",
    )
    return p.parse_args()


def _load_threshold_overrides(path: str):
    if path is None:
        return None
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("thresholds-json must contain a JSON object")
    return payload


def main() -> None:
    args = parse_args()
    thresholds = _load_threshold_overrides(args.thresholds_json)
    report = compare_hybrid_estimation_npz(
        reference_npz=args.reference_npz,
        candidate_npz=args.candidate_npz,
        thresholds=thresholds,
    )

    print(f"parity pass: {report['pass']}")
    print(f"rd key: ref={report['rd_reference_key']} cand={report['rd_candidate_key']}")
    for key in sorted(report["metrics"].keys()):
        print(f"{key}: {report['metrics'][key]:.6g}")
    if report["failures"]:
        print("failures:")
        for item in report["failures"]:
            print(
                f"  {item['metric']}: value={item['value']:.6g} limit={item['limit']:.6g}"
            )

    if args.output_json:
        Path(args.output_json).write_text(json.dumps(report, indent=2), encoding="utf-8")

    sys.exit(0 if report["pass"] else 2)


if __name__ == "__main__":
    main()

