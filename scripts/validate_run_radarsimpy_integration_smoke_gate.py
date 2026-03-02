#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_radarsimpy_smoke_gate_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        out_json = root / "smoke_summary.json"
        proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/run_radarsimpy_integration_smoke_gate.py",
                "--output-summary-json",
                str(out_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "RadarSimPy integration smoke gate completed." in proc.stdout, proc.stdout

        summary = json.loads(out_json.read_text(encoding="utf-8"))
        assert summary.get("pass") is True
        assert int(summary.get("step_count", -1)) >= 7
        assert int(summary.get("fail_count", -1)) == 0
        assert int(summary.get("pass_count", -1)) == int(summary.get("step_count", -2))

        names = {str(row.get("name")) for row in summary.get("steps", [])}
        expected = {
            "validate_radarsimpy_api_coverage_excluding_sim_lidar",
            "validate_run_radarsimpy_wrapper_integration_gate",
            "validate_run_radarsimpy_migration_stepwise",
            "validate_run_radarsimpy_periodic_parity_lock",
            "validate_build_radarsimpy_periodic_manifest_from_migration",
            "validate_install_radarsimpy_ci_workflow",
            "validate_show_radarsimpy_progress",
        }
        assert expected.issubset(names), names
        for row in summary.get("steps", []):
            assert bool(row.get("pass", False)) is True
            assert int(row.get("returncode", -1)) == 0

    print("validate_run_radarsimpy_integration_smoke_gate: pass")


if __name__ == "__main__":
    run()
