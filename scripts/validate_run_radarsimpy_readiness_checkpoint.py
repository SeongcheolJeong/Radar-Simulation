#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "run_radarsimpy_readiness_checkpoint.py"

    with tempfile.TemporaryDirectory(prefix="validate_radarsimpy_readiness_checkpoint_") as td:
        root = Path(td)
        reports = root / "reports"
        ready_json = reports / "checkpoint_ready.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        # Case 1: baseline checkpoint without runtime migration/e2e requirement should be ready.
        proc_ready = subprocess.run(
            [
                str(Path(sys.executable)),
                str(script),
                "--reports-root",
                str(reports),
                "--run-id",
                "fixture_ready",
                "--output-json",
                str(ready_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "RadarSimPy readiness checkpoint completed." in proc_ready.stdout, proc_ready.stdout
        payload_ready = json.loads(ready_json.read_text(encoding="utf-8"))
        assert payload_ready.get("report_name") == "radarsimpy_readiness_checkpoint"
        assert payload_ready.get("overall_status") == "ready"
        checks_ready = dict(payload_ready.get("checkpoint_checks") or {})
        assert bool(checks_ready.get("smoke_gate_pass", False)) is True
        assert bool(checks_ready.get("smoke_skip_flag_applied", False)) is True
        assert bool(checks_ready.get("smoke_recursion_guard_active", False)) is True
        assert bool(checks_ready.get("wrapper_gate_pass", False)) is True
        assert bool(checks_ready.get("function_api_stage_ready", False)) is True
        assert bool(checks_ready.get("migration_stage_ready", False)) is True
        assert bool(checks_ready.get("real_e2e_stage_ready", False)) is True
        assert payload_ready.get("function_status") == "ready"
        assert payload_ready.get("smoke_contains_readiness_runner_validator") is False
        assert payload_ready.get("smoke_skip_readiness_runner_validator_requested") is True
        cmd_ready = (
            payload_ready.get("commands", {})
            .get("smoke_gate", {})
            .get("cmd", [])
        )
        assert isinstance(cmd_ready, list), type(cmd_ready)
        assert "--skip-readiness-runner-validator" in [str(v) for v in cmd_ready]

        # Case 2: requiring real-e2e without an e2e rollup should block (rc=2).
        blocked_json = reports / "checkpoint_blocked.json"
        proc_blocked = subprocess.run(
            [
                str(Path(sys.executable)),
                str(script),
                "--reports-root",
                str(reports),
                "--run-id",
                "fixture_blocked",
                "--output-json",
                str(blocked_json),
                "--require-real-e2e",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc_blocked.returncode == 2, proc_blocked.returncode
        payload_blocked = json.loads(blocked_json.read_text(encoding="utf-8"))
        assert payload_blocked.get("overall_status") == "blocked"
        checks_blocked = dict(payload_blocked.get("checkpoint_checks") or {})
        assert bool(checks_blocked.get("smoke_skip_flag_applied", False)) is True
        assert bool(checks_blocked.get("smoke_recursion_guard_active", False)) is True
        assert bool(checks_blocked.get("real_e2e_stage_ready", True)) is False
        assert bool(checks_blocked.get("function_api_stage_ready", False)) is True

        # Case 3: allow-blocked should keep return code zero.
        blocked_allow_json = reports / "checkpoint_blocked_allow.json"
        proc_blocked_allow = subprocess.run(
            [
                str(Path(sys.executable)),
                str(script),
                "--reports-root",
                str(reports),
                "--run-id",
                "fixture_blocked_allow",
                "--output-json",
                str(blocked_allow_json),
                "--require-real-e2e",
                "--allow-blocked",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "overall_status: blocked" in proc_blocked_allow.stdout, proc_blocked_allow.stdout
        payload_blocked_allow = json.loads(blocked_allow_json.read_text(encoding="utf-8"))
        assert payload_blocked_allow.get("overall_status") == "blocked"
        assert payload_blocked_allow.get("function_status") == "ready"
        assert payload_blocked_allow.get("smoke_contains_readiness_runner_validator") is False
        assert payload_blocked_allow.get("smoke_skip_readiness_runner_validator_requested") is True
        cmd_blocked_allow = (
            payload_blocked_allow.get("commands", {})
            .get("smoke_gate", {})
            .get("cmd", [])
        )
        assert isinstance(cmd_blocked_allow, list), type(cmd_blocked_allow)
        assert "--skip-readiness-runner-validator" in [str(v) for v in cmd_blocked_allow]

    print("validate_run_radarsimpy_readiness_checkpoint: pass")


if __name__ == "__main__":
    run()
