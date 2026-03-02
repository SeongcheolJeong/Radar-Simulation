#!/usr/bin/env python3
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _run(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )


def _must_pass(proc: subprocess.CompletedProcess[str], label: str) -> None:
    if proc.returncode != 0:
        raise AssertionError(
            f"{label} unexpectedly failed\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}\n"
        )


def _must_fail(proc: subprocess.CompletedProcess[str], label: str, token: str) -> None:
    if proc.returncode == 0:
        raise AssertionError(
            f"{label} unexpectedly passed\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}\n"
        )
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if token not in combined:
        raise AssertionError(
            f"{label} did not include expected token: {token}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}\n"
        )


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    validator = repo_root / "scripts" / "validate_radarsimpy_readiness_checkpoint_report.py"

    with tempfile.TemporaryDirectory(prefix="validate_run_radarsimpy_readiness_report_") as td:
        root = Path(td)
        smoke_json = root / "smoke.json"
        wrapper_json = root / "wrapper.json"
        progress_json = root / "progress.json"
        function_json = root / "function.json"
        migration_json = root / "migration.json"
        _write_json(smoke_json, {"fixture": "smoke"})
        _write_json(wrapper_json, {"fixture": "wrapper"})
        _write_json(progress_json, {"fixture": "progress"})
        _write_json(function_json, {"fixture": "function"})
        _write_json(migration_json, {"fixture": "migration"})

        ready_checks = {
            "smoke_gate_pass": True,
            "smoke_skip_flag_applied": True,
            "smoke_recursion_guard_active": True,
            "wrapper_gate_pass": True,
            "progress_snapshot_generated": True,
            "progress_integration_stage_ready": True,
            "progress_wrapper_stage_ready": True,
            "function_api_stage_ready": True,
            "migration_stage_ready": True,
            "real_e2e_stage_ready": True,
        }
        ready_report = {
            "version": 1,
            "report_name": "radarsimpy_readiness_checkpoint",
            "workspace_root": str(repo_root),
            "run_id": "fixture_ready",
            "branch": "main",
            "head_commit": "abc123",
            "smoke_gate_summary_json": str(smoke_json.resolve()),
            "wrapper_gate_summary_json": str(wrapper_json.resolve()),
            "migration_summary_json": str(migration_json.resolve()),
            "function_summary_json": str(function_json.resolve()),
            "progress_snapshot_json": str(progress_json.resolve()),
            "smoke_gate_status": "ready",
            "wrapper_gate_status": "ready",
            "function_status": "ready",
            "migration_status": "ready",
            "smoke_gate_step_count": 9,
            "smoke_contains_readiness_runner_validator": False,
            "smoke_skip_readiness_runner_validator_requested": True,
            "report_contract_validator_pass": True,
            "progress_overall_ready": True,
            "checkpoint_checks": ready_checks,
            "overall_status": "ready",
            "commands": {
                "smoke_gate": {
                    "cmd": [
                        "python",
                        "scripts/run_radarsimpy_integration_smoke_gate.py",
                        "--output-summary-json",
                        "/tmp/smoke.json",
                        "--skip-readiness-runner-validator",
                    ],
                    "returncode": 0,
                    "pass": True,
                },
                "wrapper_gate": {"returncode": 0, "pass": True},
                "migration_stepwise": {"returncode": 0, "pass": True},
                "function_progress": {"returncode": 0, "pass": True},
                "progress_snapshot": {"returncode": 0, "pass": True},
                "report_contract_validator": {"returncode": 0, "pass": True},
            },
        }
        ready_path = root / "ready.json"
        _write_json(ready_path, ready_report)

        proc_ready = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator),
                "--summary-json",
                str(ready_path),
                "--require-ready",
            ],
        )
        _must_pass(proc_ready, "ready report")

        guard_without_skip = copy.deepcopy(ready_report)
        guard_without_skip["checkpoint_checks"]["smoke_skip_flag_applied"] = False
        guard_without_skip["overall_status"] = "blocked"
        guard_without_skip_path = root / "guard_without_skip.json"
        _write_json(guard_without_skip_path, guard_without_skip)
        proc_guard_without_skip = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator),
                "--summary-json",
                str(guard_without_skip_path),
            ],
        )
        _must_fail(
            proc_guard_without_skip,
            "guard_without_skip report",
            "smoke_recursion_guard_active requires smoke_skip_flag_applied=true",
        )

        skip_requested_mismatch = copy.deepcopy(ready_report)
        skip_requested_mismatch["smoke_skip_readiness_runner_validator_requested"] = False
        skip_requested_mismatch_path = root / "skip_requested_mismatch.json"
        _write_json(skip_requested_mismatch_path, skip_requested_mismatch)
        proc_skip_requested_mismatch = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator),
                "--summary-json",
                str(skip_requested_mismatch_path),
            ],
        )
        _must_fail(
            proc_skip_requested_mismatch,
            "skip_requested_mismatch report",
            "smoke_skip_readiness_runner_validator_requested mismatch",
        )

        cmd_skip_mismatch = copy.deepcopy(ready_report)
        cmd_skip_mismatch["commands"]["smoke_gate"]["cmd"] = [
            "python",
            "scripts/run_radarsimpy_integration_smoke_gate.py",
            "--output-summary-json",
            "/tmp/smoke.json",
        ]
        cmd_skip_mismatch_path = root / "cmd_skip_mismatch.json"
        _write_json(cmd_skip_mismatch_path, cmd_skip_mismatch)
        proc_cmd_skip_mismatch = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator),
                "--summary-json",
                str(cmd_skip_mismatch_path),
            ],
        )
        _must_fail(
            proc_cmd_skip_mismatch,
            "cmd_skip_mismatch report",
            "commands.smoke_gate.cmd skip-flag mismatch",
        )

        cmd_missing = copy.deepcopy(ready_report)
        del cmd_missing["commands"]["smoke_gate"]["cmd"]
        cmd_missing_path = root / "cmd_missing.json"
        _write_json(cmd_missing_path, cmd_missing)
        proc_cmd_missing = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator),
                "--summary-json",
                str(cmd_missing_path),
            ],
        )
        _must_fail(
            proc_cmd_missing,
            "cmd_missing report",
            "commands.smoke_gate.cmd must be non-empty list",
        )

        mismatch = copy.deepcopy(ready_report)
        mismatch["overall_status"] = "blocked"
        mismatch_path = root / "mismatch.json"
        _write_json(mismatch_path, mismatch)
        proc_mismatch = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator),
                "--summary-json",
                str(mismatch_path),
            ],
        )
        _must_fail(proc_mismatch, "mismatch report", "overall_status mismatch")

        blocked = copy.deepcopy(ready_report)
        blocked["checkpoint_checks"]["real_e2e_stage_ready"] = False
        blocked["overall_status"] = "blocked"
        blocked["wrapper_gate_status"] = "ready"
        blocked["function_status"] = "ready"
        blocked_path = root / "blocked.json"
        _write_json(blocked_path, blocked)
        proc_blocked = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator),
                "--summary-json",
                str(blocked_path),
            ],
        )
        _must_pass(proc_blocked, "blocked report")

        proc_blocked_require_ready = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator),
                "--summary-json",
                str(blocked_path),
                "--require-ready",
            ],
        )
        _must_fail(proc_blocked_require_ready, "blocked report require-ready", "overall_status must be ready")

    print("validate_run_radarsimpy_readiness_checkpoint_report: pass")


if __name__ == "__main__":
    run()
