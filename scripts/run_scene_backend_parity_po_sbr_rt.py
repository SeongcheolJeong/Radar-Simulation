#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scene_backend_parity_cases import run_scene_backend_parity_case


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run the canonical PO-SBR RT scene-backend parity case and emit a stable report."
    )
    p.add_argument(
        "--output-root",
        default="data/runtime_golden_path/scene_backend_parity_po_sbr_rt_latest",
        help="Directory for persistent parity artifacts.",
    )
    p.add_argument(
        "--output-json",
        default="docs/reports/scene_backend_parity_po_sbr_rt_latest.json",
        help="Stable report JSON path.",
    )
    p.add_argument("--python-bin", default="", help="Optional Python binary for nested runner execution.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    report = run_scene_backend_parity_case(
        case_name="po_sbr_rt",
        repo_root=repo_root,
        output_root=Path(args.output_root),
        output_json=Path(args.output_json),
        python_bin=str(args.python_bin),
    )
    print("run_scene_backend_parity_po_sbr_rt: done")
    print(f"pass={report['pass']}")
    print(f"output_json={Path(args.output_json).expanduser().resolve()}")
    if not bool(report["pass"]):
        sys.exit(2)


if __name__ == "__main__":
    main()
