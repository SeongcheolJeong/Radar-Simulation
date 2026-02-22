#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_m14_6_closure_readiness_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        out_json = root / "readiness.json"
        missing_report = root / "missing_linux_report.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        proc = subprocess.run(
            [
                "python3",
                "scripts/run_m14_6_closure_readiness.py",
                "--linux-summary-json",
                str(missing_report),
                "--output-summary-json",
                str(out_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "M14.6 closure readiness check completed." in proc.stdout, proc.stdout

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload.get("ready") is False
        assert isinstance(payload.get("missing_items"), list)
        assert "linux_executed_report_missing" in payload["missing_items"]
        assert isinstance(payload.get("required_files_count"), int)
        assert isinstance(payload.get("missing_required_files"), list)
        assert payload.get("report_exists") is False

    print("validate_run_m14_6_closure_readiness: pass")


if __name__ == "__main__":
    run()
