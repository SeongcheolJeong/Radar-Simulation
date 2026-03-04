#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _pick_python_bin(repo_root: Path) -> str:
    venv_python = repo_root / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return str(Path(sys.executable))


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    python_bin = _pick_python_bin(repo_root=repo_root)

    with tempfile.TemporaryDirectory(prefix="validate_run_radarsimpy_production_gate_") as td:
        root = Path(td)
        summary_json = root / "summary.json"
        checkpoint_json = root / "checkpoint.json"
        search_root = root / "no_license_here"
        search_root.mkdir(parents=True, exist_ok=True)

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        # Case 1: missing license + allow-blocked -> rc=0 with blocked status.
        proc_allow = subprocess.run(
            [
                python_bin,
                "scripts/run_radarsimpy_production_release_gate.py",
                "--output-json",
                str(summary_json),
                "--checkpoint-output-json",
                str(checkpoint_json),
                "--search-root",
                str(search_root),
                "--search-max-depth",
                "2",
                "--allow-blocked",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "RadarSimPy production release gate completed." in proc_allow.stdout, proc_allow.stdout
        payload = json.loads(summary_json.read_text(encoding="utf-8"))
        assert payload.get("production_gate_status") == "blocked"
        assert payload.get("selected_license_file") == ""
        blockers = set(str(x) for x in (payload.get("blockers") or []))
        assert "license_file_missing" in blockers
        checkpoint_run = payload.get("checkpoint_run") or {}
        assert checkpoint_run.get("skipped") is True

        # Case 2: missing license without allow-blocked -> rc=2.
        summary_json2 = root / "summary2.json"
        proc_blocked = subprocess.run(
            [
                python_bin,
                "scripts/run_radarsimpy_production_release_gate.py",
                "--output-json",
                str(summary_json2),
                "--checkpoint-output-json",
                str(checkpoint_json),
                "--search-root",
                str(search_root),
                "--search-max-depth",
                "2",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc_blocked.returncode == 2, proc_blocked.returncode
        payload2 = json.loads(summary_json2.read_text(encoding="utf-8"))
        assert payload2.get("production_gate_status") == "blocked"
        blockers2 = set(str(x) for x in (payload2.get("blockers") or []))
        assert "license_file_missing" in blockers2

    print("validate_run_radarsimpy_production_release_gate: pass")


if __name__ == "__main__":
    run()
