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
    validator_script = repo_root / "scripts" / "validate_po_sbr_myproject_readiness_checkpoint_report.py"

    with tempfile.TemporaryDirectory(
        prefix="validate_run_po_sbr_myproject_readiness_checkpoint_report_"
    ) as td:
        root = Path(td)
        run_id = "2026_03_02_fixture"
        head_tail = run_id.rsplit("_", 1)[-1]
        function_test_json = root / "function_test.json"
        bundle_json = root / "bundle.json"
        gate_lock_json = root / "gate_lock.json"
        local_ready_json = root / "local_ready.json"
        baseline_manifest_json = root / "baseline_manifest.json"
        baseline_drift_json = root / f"baseline_drift_{run_id}.json"
        avx_gate_json = root / "avx_gate.json"
        avx_gate_blocked_json = root / "avx_gate_blocked.json"
        avx_matrix_json = root / "avx_matrix.json"
        em_policy_json = root / "em_solver_packaging_policy.json"
        em_reference_locks_md = root / "reference-locks.md"
        progress_json = root / f"progress_{run_id}.json"

        _write_json(function_test_json, {"overall_status": "ready"})
        _write_json(bundle_json, {"fixture": "bundle"})
        _write_json(gate_lock_json, {"fixture": "gate_lock"})
        _write_json(local_ready_json, {"summary": {"overall_status": "ready"}})
        _write_json(baseline_manifest_json, {"fixture": "baseline_manifest"})
        _write_json(baseline_drift_json, {"drift_verdict": "match", "difference_count": 0})
        _write_json(avx_gate_json, {"developer_gate_status": "ready"})
        _write_json(avx_gate_blocked_json, {"developer_gate_status": "blocked"})
        _write_json(avx_matrix_json, {"fixture": "avx_matrix"})
        _write_json(
            em_policy_json,
            {
                "version": 1,
                "policy_id": "em_solver_packaging_license_boundary_v1",
            },
        )
        em_reference_locks_md.write_text(
            "\n".join(
                [
                    "# Reference Locks",
                    "",
                    "- openEMS: " + ("a" * 40),
                    "- CSXCAD: " + ("b" * 40),
                    "- gprMax: " + ("c" * 40),
                ]
            ),
            encoding="utf-8",
        )
        _write_json(progress_json, {"overall_ready": True})

        refs_ready = {
            "function_test_summary_json": function_test_json,
            "bundle_summary_json": bundle_json,
            "gate_lock_summary_json": gate_lock_json,
            "local_ready_summary_json": local_ready_json,
            "baseline_manifest_json": baseline_manifest_json,
            "baseline_drift_report_json": baseline_drift_json,
            "avx_developer_gate_summary_json": avx_gate_json,
            "avx_developer_gate_matrix_summary_json": avx_matrix_json,
            "em_solver_policy_json": em_policy_json,
            "em_solver_reference_locks_md": em_reference_locks_md,
            "progress_snapshot_json": progress_json,
        }

        ready_report = {
            "version": 1,
            "report_name": "po_sbr_myproject_readiness_checkpoint",
            "generated_at_utc": "2026-03-02T00:00:00+00:00",
            "workspace_root": str(repo_root),
            "run_id": run_id,
            "branch": "fixture_branch",
            "head_commit": f"{head_tail}_commit_hash",
            **{key: str(path.resolve()) for key, path in refs_ready.items()},
            "function_test_overall_status": "ready",
            "local_ready_overall_status": "ready",
            "baseline_drift_verdict": "match",
            "baseline_drift_difference_count": 0,
            "avx_developer_gate_status": "ready",
            "em_policy_validator_status": "pass",
            "post_change_gate_validator_status": "pass",
            "closure_report_validator_status": "pass",
            "progress_snapshot_overall_ready": True,
            "progress_snapshot_validator_status": "pass",
            "hook_selftest_validator_status": "pass",
            "checkpoint_checks": {
                "function_test_ready": True,
                "local_ready_ready": True,
                "baseline_drift_match": True,
                "avx_developer_gate_ready": True,
                "em_policy_validator_ok": True,
                "post_change_gate_validator_ok": True,
                "closure_report_validator_ok": True,
                "progress_snapshot_overall_ready": True,
                "progress_snapshot_validator_ok": True,
                "hook_selftest_validator_ok": True,
            },
            "overall_status": "ready",
        }

        ready_path = root / "checkpoint_ready.json"
        _write_json(ready_path, ready_report)

        proc_ready = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator_script),
                "--summary-json",
                str(ready_path),
                "--require-ready",
            ],
        )
        _must_pass(proc_ready, "ready report")

        mismatch_report = copy.deepcopy(ready_report)
        mismatch_report["checkpoint_checks"]["avx_developer_gate_ready"] = False
        mismatch_path = root / "checkpoint_mismatch.json"
        _write_json(mismatch_path, mismatch_report)

        proc_mismatch = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator_script),
                "--summary-json",
                str(mismatch_path),
            ],
        )
        _must_fail(
            proc_mismatch,
            "mismatched checkpoint_checks report",
            "checkpoint_checks.avx_developer_gate_ready mismatch",
        )

        source_mismatch_report = copy.deepcopy(ready_report)
        source_mismatch_report["function_test_overall_status"] = "blocked"
        source_mismatch_report["checkpoint_checks"]["function_test_ready"] = False
        source_mismatch_report["overall_status"] = "blocked"
        source_mismatch_path = root / "checkpoint_source_mismatch.json"
        _write_json(source_mismatch_path, source_mismatch_report)

        proc_source_mismatch = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator_script),
                "--summary-json",
                str(source_mismatch_path),
            ],
        )
        _must_fail(
            proc_source_mismatch,
            "function-test source mismatch report",
            "function_test_overall_status mismatch with function-test report",
        )

        blocked_report = copy.deepcopy(ready_report)
        blocked_report["avx_developer_gate_summary_json"] = str(avx_gate_blocked_json.resolve())
        blocked_report["avx_developer_gate_status"] = "blocked"
        blocked_report["checkpoint_checks"]["avx_developer_gate_ready"] = False
        blocked_report["overall_status"] = "blocked"
        blocked_path = root / "checkpoint_blocked.json"
        _write_json(blocked_path, blocked_report)

        proc_blocked = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator_script),
                "--summary-json",
                str(blocked_path),
            ],
        )
        _must_pass(proc_blocked, "blocked report without require-ready")

        proc_blocked_require_ready = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator_script),
                "--summary-json",
                str(blocked_path),
                "--require-ready",
            ],
        )
        _must_fail(
            proc_blocked_require_ready,
            "blocked report with require-ready",
            "overall_status must be ready",
        )

    print("validate_run_po_sbr_myproject_readiness_checkpoint_report: pass")


if __name__ == "__main__":
    run()
