#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate M14.6 closure readiness from artifacts and report evidence")
    p.add_argument(
        "--linux-summary-json",
        default="docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json",
        help="Expected Linux strict pilot summary JSON path",
    )
    p.add_argument("--output-summary-json", required=True, help="Output readiness summary JSON path")
    return p.parse_args()


def _required_paths(repo_root: Path) -> List[Path]:
    rel = [
        "src/avxsim/runtime_providers/po_sbr_rt_provider.py",
        "scripts/run_scene_runtime_po_sbr_pilot.py",
        "scripts/run_m14_6_po_sbr_linux_strict.sh",
        "scripts/validate_scene_runtime_po_sbr_executed_report.py",
        "scripts/validate_po_sbr_runtime_provider_stubbed.py",
        "scripts/validate_scene_runtime_po_sbr_provider_integration_stubbed.py",
        "docs/112_scene_runtime_po_sbr_pilot_contract.md",
        "docs/113_po_sbr_linux_runtime_runbook.md",
    ]
    return [repo_root / x for x in rel]


def _run_executed_report_validator(repo_root: Path, summary_json: Path) -> Dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")
    proc = subprocess.run(
        [
            str(Path(sys.executable)),
            "scripts/validate_scene_runtime_po_sbr_executed_report.py",
            "--summary-json",
            str(summary_json),
        ],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
    )
    return {
        "ok": bool(proc.returncode == 0),
        "return_code": int(proc.returncode),
        "stdout": str(proc.stdout).strip(),
        "stderr": str(proc.stderr).strip(),
    }


def _build_readiness_summary(repo_root: Path, linux_summary_json: Path) -> Dict[str, Any]:
    missing_items: List[str] = []
    required_files = _required_paths(repo_root)
    missing_required_files = [str(p) for p in required_files if not p.exists()]
    if len(missing_required_files) > 0:
        missing_items.append("missing_required_files")

    report_exists = linux_summary_json.exists()
    report_validation = None
    if not report_exists:
        missing_items.append("linux_executed_report_missing")
    else:
        report_validation = _run_executed_report_validator(repo_root=repo_root, summary_json=linux_summary_json)
        if not bool(report_validation.get("ok", False)):
            missing_items.append("linux_executed_report_invalid")

    ready = len(missing_items) == 0
    return {
        "repo_root": str(repo_root),
        "linux_summary_json": str(linux_summary_json),
        "ready": bool(ready),
        "missing_items": missing_items,
        "required_files_count": int(len(required_files)),
        "missing_required_files": missing_required_files,
        "report_exists": bool(report_exists),
        "report_validation": report_validation,
    }


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    linux_summary_json = Path(args.linux_summary_json).expanduser()
    if not linux_summary_json.is_absolute():
        linux_summary_json = (repo_root / linux_summary_json).resolve()
    else:
        linux_summary_json = linux_summary_json.resolve()

    summary = _build_readiness_summary(repo_root=repo_root, linux_summary_json=linux_summary_json)
    out = Path(args.output_summary_json).expanduser()
    if not out.is_absolute():
        out = (repo_root / out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("M14.6 closure readiness check completed.")
    print(f"  ready: {summary['ready']}")
    print(f"  missing_items: {summary['missing_items']}")
    print(f"  output_summary_json: {out}")


if __name__ == "__main__":
    main()
