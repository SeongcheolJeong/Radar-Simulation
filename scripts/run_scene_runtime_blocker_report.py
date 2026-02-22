#!/usr/bin/env python3
import argparse
from pathlib import Path

from avxsim.runtime_blockers import (
    build_runtime_blocker_report,
    load_runtime_probe_summary_json,
    save_runtime_blocker_report_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build blocker report from runtime probe summary")
    p.add_argument("--probe-summary-json", required=True, help="Input runtime probe summary JSON path")
    p.add_argument("--output-report-json", required=True, help="Output blocker report JSON path")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    probe = load_runtime_probe_summary_json(args.probe_summary_json)
    report = build_runtime_blocker_report(probe_summary=probe)
    save_runtime_blocker_report_json(report, args.output_report_json)

    out = Path(args.output_report_json)
    print("Scene runtime blocker report completed.")
    print(f"  ready_count: {report['ready_count']}")
    print(f"  blocked_count: {report['blocked_count']}")
    print(f"  next_recommended_runtime: {report['next_recommended_runtime']}")
    print(f"  output_report_json: {out}")


if __name__ == "__main__":
    main()
