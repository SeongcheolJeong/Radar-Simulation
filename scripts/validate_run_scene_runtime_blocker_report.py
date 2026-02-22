#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_runtime_blocker_report_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        probe_json = root / "probe_summary.json"
        report_json = root / "blocker_report.json"

        probe_payload = {
            "runtime_report": {
                "runtime_a": {
                    "ready": True,
                    "status": "ready",
                    "blockers": [],
                    "repo_candidates": ["external/a"],
                    "missing_required_modules": [],
                    "supported_systems": ["Darwin", "Linux"],
                },
                "runtime_b": {
                    "ready": False,
                    "status": "blocked",
                    "blockers": ["missing_repo", "missing_required_modules"],
                    "repo_candidates": ["external/b"],
                    "missing_required_modules": ["foo", "bar"],
                    "supported_systems": ["Linux"],
                },
            }
        }
        probe_json.write_text(json.dumps(probe_payload, indent=2), encoding="utf-8")

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        proc = subprocess.run(
            [
                "python3",
                "scripts/run_scene_runtime_blocker_report.py",
                "--probe-summary-json",
                str(probe_json),
                "--output-report-json",
                str(report_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Scene runtime blocker report completed." in proc.stdout, proc.stdout

        report = json.loads(report_json.read_text(encoding="utf-8"))
        assert int(report["ready_count"]) == 1
        assert int(report["blocked_count"]) == 1
        assert report["next_recommended_runtime"] == "runtime_a"
        entries = report["entries"]
        assert isinstance(entries, list) and len(entries) == 2
        entry_b = [x for x in entries if x["runtime_name"] == "runtime_b"][0]
        assert "add/cloned repo candidate under workspace: external/b" in entry_b["recommended_actions"]
        assert "install missing Python modules: foo bar" in entry_b["recommended_actions"]

    print("validate_run_scene_runtime_blocker_report: pass")


if __name__ == "__main__":
    run()
