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
    with tempfile.TemporaryDirectory(prefix="validate_run_radarsimpy_wrapper_gate_") as td:
        summary_json = Path(td) / "summary.json"
        proc = subprocess.run(
            [
                python_bin,
                "scripts/run_radarsimpy_wrapper_integration_gate.py",
                "--output-summary-json",
                str(summary_json),
            ],
            cwd=str(repo_root),
            env={**os.environ, "PYTHONPATH": str(repo_root / "src")},
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                "wrapper integration gate failed\n"
                f"stdout:\n{proc.stdout}\n"
                f"stderr:\n{proc.stderr}\n"
            )
        if "RadarSimPy wrapper integration gate completed." not in proc.stdout:
            raise AssertionError(proc.stdout)
        payload = json.loads(summary_json.read_text(encoding="utf-8"))
        assert payload["pass"] is True
        assert payload["fail_count"] == 0
        names = [str(item.get("check_name", "")) for item in payload.get("checks", [])]
        expected = {
            "wrapper_entrypoint_guard",
            "api_coverage_excluding_sim_lidar",
            "runtime_provider_integration_stubbed",
            "periodic_parity_lock_runner",
            "runtime_pilot_runner",
            "migration_stepwise_runner",
        }
        assert expected.issubset(set(names)), names
    print("validate_run_radarsimpy_wrapper_integration_gate: pass")


if __name__ == "__main__":
    run()
