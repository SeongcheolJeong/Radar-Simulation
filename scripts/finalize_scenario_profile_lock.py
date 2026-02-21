#!/usr/bin/env python3
import argparse
import sys

from avxsim.profile_lock import (
    build_profile_lock_report,
    load_replay_report_json,
    save_profile_lock_report_json,
    write_locked_profiles,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Finalize scenario profile lock from replay batch report")
    p.add_argument("--replay-report-json", required=True)
    p.add_argument("--output-lock-json", required=True)
    p.add_argument(
        "--output-locked-profile-dir",
        default=None,
        help="Optional directory to write *.locked.json profiles",
    )
    p.add_argument(
        "--min-pass-rate",
        type=float,
        default=1.0,
        help="Minimum pass rate required per case to lock",
    )
    p.add_argument(
        "--max-case-fail-count",
        type=int,
        default=0,
        help="Maximum failing candidates allowed per case",
    )
    p.add_argument(
        "--require-motion-defaults-enabled",
        action="store_true",
        help="Require motion_compensation_defaults.enabled=True for lock pass",
    )
    p.add_argument(
        "--allow-unlocked",
        action="store_true",
        help="Return 0 even when one or more cases are unlocked",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    replay = load_replay_report_json(args.replay_report_json)
    report = build_profile_lock_report(
        replay_report=replay,
        policy={
            "min_pass_rate": float(args.min_pass_rate),
            "max_case_fail_count": int(args.max_case_fail_count),
            "require_motion_defaults_enabled": bool(args.require_motion_defaults_enabled),
        },
    )

    if args.output_locked_profile_dir is not None:
        written = write_locked_profiles(
            replay_report=replay,
            lock_report=report,
            output_dir=args.output_locked_profile_dir,
            replay_report_json=args.replay_report_json,
        )
        report["locked_profiles"] = written

    save_profile_lock_report_json(args.output_lock_json, report)

    s = report["summary"]
    print("Scenario profile lock finalization completed.")
    print(f"  cases: {s['case_count']}")
    print(f"  locked: {s['locked_count']}")
    print(f"  unlocked: {s['unlocked_count']}")
    print(f"  overall_lock_pass: {report['overall_lock_pass']}")
    print(f"  output: {args.output_lock_json}")

    if (not report["overall_lock_pass"]) and (not args.allow_unlocked):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
