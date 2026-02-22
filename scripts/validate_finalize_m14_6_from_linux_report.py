#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_finalize_m14_6_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        linux_summary_missing = root / "scene_runtime_po_sbr_pilot_m14_6_linux_missing.json"
        closure_json = root / "closure_readiness.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        proc = subprocess.run(
            [
                "python3",
                "scripts/finalize_m14_6_from_linux_report.py",
                "--linux-summary-json",
                str(linux_summary_missing),
                "--closure-summary-json",
                str(closure_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 2, proc.stdout + "\n" + proc.stderr
        assert "M14.6 finalize check: not ready" in proc.stdout, proc.stdout
        assert closure_json.exists(), "closure readiness json should be generated even on not-ready"
        payload = json.loads(closure_json.read_text(encoding="utf-8"))
        assert payload.get("ready") is False
        missing_items = payload.get("missing_items")
        assert isinstance(missing_items, list)
        assert "linux_executed_report_missing" in missing_items

    print("validate_finalize_m14_6_from_linux_report: pass")


if __name__ == "__main__":
    run()
