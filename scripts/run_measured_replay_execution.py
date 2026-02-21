#!/usr/bin/env python3
import argparse
import sys

from avxsim.measured_replay import (
    run_measured_replay_plan_json,
    save_measured_replay_summary_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Execute measured replay plan (batch replay + profile lock finalization)"
    )
    p.add_argument("--plan-json", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--output-summary-json", required=True)
    p.add_argument(
        "--default-min-pass-rate",
        type=float,
        default=1.0,
        help="Default lock policy min pass rate for packs",
    )
    p.add_argument(
        "--default-max-case-fail-count",
        type=int,
        default=0,
        help="Default lock policy max fail count for packs",
    )
    p.add_argument(
        "--default-require-motion-defaults-enabled",
        action="store_true",
        help="Default lock policy: require motion_compensation_defaults.enabled",
    )
    p.add_argument(
        "--allow-unlocked",
        action="store_true",
        help="Return 0 even when one or more packs have unlocked scenarios",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_measured_replay_plan_json(
        plan_json=args.plan_json,
        output_root=args.output_root,
        default_lock_policy={
            "min_pass_rate": float(args.default_min_pass_rate),
            "max_case_fail_count": int(args.default_max_case_fail_count),
            "require_motion_defaults_enabled": bool(
                args.default_require_motion_defaults_enabled
            ),
        },
    )
    save_measured_replay_summary_json(args.output_summary_json, summary)

    s = summary["summary"]
    print("Measured replay execution completed.")
    print(f"  packs: {s['pack_count']}")
    print(f"  cases: {s['case_count']}")
    print(f"  locked: {s['locked_count']}")
    print(f"  unlocked: {s['unlocked_count']}")
    print(f"  overall_lock_pass: {summary['overall_lock_pass']}")
    print(f"  output_summary: {args.output_summary_json}")

    if (not summary["overall_lock_pass"]) and (not args.allow_unlocked):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
