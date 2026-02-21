#!/usr/bin/env python3
import argparse
import sys

from avxsim.replay_batch import run_replay_manifest, save_replay_report_json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run moving-target replay batch evaluation")
    p.add_argument("--manifest-json", required=True, help="Replay manifest JSON")
    p.add_argument("--output-json", required=True, help="Output report JSON")
    p.add_argument(
        "--allow-failures",
        action="store_true",
        help="Return 0 even when some candidates fail",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    report = run_replay_manifest(args.manifest_json)
    save_replay_report_json(args.output_json, report)

    s = report["summary"]
    print("Replay batch evaluation completed.")
    print(f"  cases: {s['case_count']}")
    print(f"  candidates: {s['candidate_count']}")
    print(f"  pass: {s['pass_count']}")
    print(f"  fail: {s['fail_count']}")
    print(f"  pass_rate: {s['pass_rate']:.6f}")
    print(f"  output: {args.output_json}")

    if s["fail_count"] > 0 and not args.allow_failures:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()

