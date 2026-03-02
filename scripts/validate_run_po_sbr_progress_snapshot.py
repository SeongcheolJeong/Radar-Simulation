#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _stage(payload: dict, name: str) -> dict:
    stages = payload.get("stages")
    if not isinstance(stages, list):
        raise AssertionError("stages must be a list")
    for row in stages:
        if isinstance(row, dict) and str(row.get("name", "")) == name:
            return row
    raise AssertionError(f"stage not found: {name}")


def _run(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(repo_root, ["git", *args])


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    with tempfile.TemporaryDirectory(prefix="validate_run_po_sbr_progress_snapshot_") as td:
        root = Path(td)
        reports = root / "reports"

        _write_json(
            reports / "po_sbr_physical_full_track_merged_checkpoint_2026_03_02_fixture.json",
            {
                "ready": True,
                "status": {
                    "matrix_status": "ready",
                    "full_track_status": "ready",
                    "gate_lock_status": "ready",
                    "stability_status": "stable",
                    "hardening_status": "hardened",
                    "realism_gate_candidate_status": "ready",
                },
                "generated_from_head_commit": "fixture_head",
            },
        )
        _write_json(
            reports / "po_sbr_operator_handoff_closure_2026_03_02_fixture.json",
            {
                "overall_status": "ready",
                "frontend_timeline_import_audit": {
                    "validator_status": "pass",
                    "api_regression_status": "pass",
                },
                "merged_full_track": {"ready": True},
            },
        )
        _write_json(
            reports / "po_sbr_post_change_gate_2026_03_02_fixture.json",
            {
                "overall_status": "ready",
                "closure_required": True,
                "closure_status": "pass",
                "forced": True,
            },
        )
        _write_json(
            reports / "po_sbr_local_ready_regression_2026_03_02_pc_self.json",
            {
                "summary": {
                    "overall_status": "ready",
                    "golden_path_status": "ready",
                    "kpi_campaign_status": "ready",
                    "kpi_scenario_matrix_status": "ready",
                    "gate_lock_status": "ready",
                }
            },
        )
        _write_json(
            reports / "po_sbr_local_ready_baseline_drift_2026_03_02_pc_self.json",
            {
                "drift_verdict": "match",
                "difference_count": 0,
            },
        )

        hooks_before_proc = _git(repo_root, "config", "--get", "core.hooksPath")
        hooks_before = hooks_before_proc.stdout.strip() if hooks_before_proc.returncode == 0 else None
        set_proc = _git(repo_root, "config", "core.hooksPath", ".githooks")
        if set_proc.returncode != 0:
            raise RuntimeError(
                "failed to set core.hooksPath for validator run:\n"
                f"stdout:\n{set_proc.stdout}\n"
                f"stderr:\n{set_proc.stderr}\n"
            )

        try:
            out_missing = root / "progress_missing_myproject.json"
            proc_missing = _run(
                repo_root,
                [
                    str(Path(sys.executable)),
                    "scripts/show_po_sbr_progress.py",
                    "--reports-root",
                    str(reports),
                    "--strict-ready",
                    "--output-json",
                    str(out_missing),
                ],
            )
            if proc_missing.returncode != 0:
                raise AssertionError(
                    "show_po_sbr_progress missing-myproject case failed\n"
                    f"stdout:\n{proc_missing.stdout}\n"
                    f"stderr:\n{proc_missing.stderr}\n"
                )
            payload_missing = _load_json(out_missing)
            stage_missing = _stage(payload_missing, "myproject_readiness_checkpoint")
            assert stage_missing.get("status") == "missing", stage_missing.get("status")
            assert bool(stage_missing.get("required", True)) is False
            assert bool(payload_missing.get("overall_ready", False)) is True

            _write_json(
                reports / "po_sbr_myproject_readiness_checkpoint_2026_03_02_fixture.json",
                {
                    "report_name": "po_sbr_myproject_readiness_checkpoint",
                    "overall_status": "ready",
                    "avx_developer_gate_status": "ready",
                    "function_test_overall_status": "ready",
                    "local_ready_overall_status": "ready",
                    "baseline_drift_verdict": "match",
                    "baseline_drift_difference_count": 0,
                    "progress_snapshot_overall_ready": True,
                    "post_change_gate_validator_status": "pass",
                    "progress_snapshot_validator_status": "pass",
                    "hook_selftest_validator_status": "pass",
                    "checkpoint_checks": {
                        "function_test_ready": True,
                        "local_ready_ready": True,
                        "baseline_drift_match": True,
                        "avx_developer_gate_ready": True,
                        "post_change_gate_validator_ok": True,
                        "progress_snapshot_overall_ready": True,
                        "progress_snapshot_validator_ok": True,
                        "hook_selftest_validator_ok": True,
                    },
                },
            )

            out_ready = root / "progress_ready_myproject.json"
            proc_ready = _run(
                repo_root,
                [
                    str(Path(sys.executable)),
                    "scripts/show_po_sbr_progress.py",
                    "--reports-root",
                    str(reports),
                    "--strict-ready",
                    "--output-json",
                    str(out_ready),
                ],
            )
            if proc_ready.returncode != 0:
                raise AssertionError(
                    "show_po_sbr_progress ready-myproject case failed\n"
                    f"stdout:\n{proc_ready.stdout}\n"
                    f"stderr:\n{proc_ready.stderr}\n"
                )
            payload_ready = _load_json(out_ready)
            stage_ready = _stage(payload_ready, "myproject_readiness_checkpoint")
            assert stage_ready.get("status") == "ready", stage_ready.get("status")
            assert bool(stage_ready.get("required", True)) is False
            details = stage_ready.get("details")
            if not isinstance(details, dict):
                raise AssertionError("myproject checkpoint stage details must be an object")
            assert str(details.get("function_test_overall_status", "")) == "ready"
            assert str(details.get("local_ready_overall_status", "")) == "ready"
            assert str(details.get("baseline_drift_verdict", "")) == "match"
            assert int(details.get("baseline_drift_difference_count", -1)) == 0
            assert bool(details.get("progress_snapshot_overall_ready", False)) is True
            assert str(details.get("post_change_gate_validator_status", "")) == "pass"
            assert str(details.get("progress_snapshot_validator_status", "")) == "pass"
            assert str(details.get("hook_selftest_validator_status", "")) == "pass"
            assert bool(details.get("checkpoint_checks_ready", False)) is True
            assert bool(payload_ready.get("overall_ready", False)) is True

            _write_json(
                reports / "po_sbr_myproject_readiness_checkpoint_2026_03_02_fixture.json",
                {
                    "report_name": "po_sbr_myproject_readiness_checkpoint",
                    "overall_status": "blocked",
                    "avx_developer_gate_status": "blocked",
                    "function_test_overall_status": "ready",
                    "local_ready_overall_status": "ready",
                    "baseline_drift_verdict": "match",
                    "baseline_drift_difference_count": 0,
                    "progress_snapshot_overall_ready": True,
                    "post_change_gate_validator_status": "pass",
                    "progress_snapshot_validator_status": "pass",
                    "hook_selftest_validator_status": "pass",
                    "checkpoint_checks": {
                        "function_test_ready": True,
                        "local_ready_ready": True,
                        "baseline_drift_match": True,
                        "avx_developer_gate_ready": False,
                        "post_change_gate_validator_ok": True,
                        "progress_snapshot_overall_ready": True,
                        "progress_snapshot_validator_ok": True,
                        "hook_selftest_validator_ok": True,
                    },
                },
            )

            out_blocked = root / "progress_blocked_myproject.json"
            proc_blocked = _run(
                repo_root,
                [
                    str(Path(sys.executable)),
                    "scripts/show_po_sbr_progress.py",
                    "--reports-root",
                    str(reports),
                    "--strict-ready",
                    "--output-json",
                    str(out_blocked),
                ],
            )
            if proc_blocked.returncode != 0:
                raise AssertionError(
                    "show_po_sbr_progress blocked-myproject case failed\n"
                    f"stdout:\n{proc_blocked.stdout}\n"
                    f"stderr:\n{proc_blocked.stderr}\n"
                )
            payload_blocked = _load_json(out_blocked)
            stage_blocked = _stage(payload_blocked, "myproject_readiness_checkpoint")
            assert stage_blocked.get("status") == "blocked", stage_blocked.get("status")
            assert bool(stage_blocked.get("required", True)) is False
            details_blocked = stage_blocked.get("details")
            if not isinstance(details_blocked, dict):
                raise AssertionError("blocked myproject checkpoint stage details must be an object")
            assert str(details_blocked.get("overall_status", "")) == "blocked"
            assert str(details_blocked.get("avx_developer_gate_status", "")) == "blocked"
            assert bool(details_blocked.get("checkpoint_checks_ready", True)) is False
            assert bool(payload_blocked.get("overall_ready", False)) is True
        finally:
            if hooks_before is None:
                _git(repo_root, "config", "--unset", "core.hooksPath")
            else:
                _git(repo_root, "config", "core.hooksPath", hooks_before)

    print("validate_run_po_sbr_progress_snapshot: pass")


if __name__ == "__main__":
    run()
