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
    validator_script = (
        repo_root / "scripts" / "validate_po_sbr_operator_handoff_closure_report.py"
    )

    with tempfile.TemporaryDirectory(
        prefix="validate_run_po_sbr_operator_handoff_closure_report_"
    ) as td:
        root = Path(td)
        merged_ready_json = root / "merged_ready.json"
        merged_blocked_json = root / "merged_blocked.json"
        avx_ready_json = root / "avx_ready.json"
        avx_blocked_json = root / "avx_blocked.json"
        avx_matrix_json = root / "avx_matrix.json"
        em_policy_json = root / "em_policy.json"
        em_reference_locks_md = root / "reference-locks.md"

        _write_json(merged_ready_json, {"ready": True})
        _write_json(merged_blocked_json, {"ready": False})
        _write_json(avx_ready_json, {"developer_gate_status": "ready"})
        _write_json(avx_blocked_json, {"developer_gate_status": "blocked"})
        _write_json(avx_matrix_json, {"report_name": "avx_export_benchmark_matrix_summary"})
        _write_json(
            em_policy_json,
            {"version": 1, "policy_id": "em_solver_packaging_license_boundary_v1"},
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

        base_ready = {
            "report_name": "po_sbr_operator_handoff_closure",
            "generated_at_utc": "2026-03-02T00:00:00+00:00",
            "workspace_root": str(repo_root.resolve()),
            "branch": "fixture_branch",
            "head_commit": "fixture_head_commit",
            "frontend_timeline_import_audit": {
                "milestones": ["M17.97", "M17.98", "M17.99", "M17.100", "M17.101"],
                "validator_status": "pass",
                "api_regression_status": "pass",
            },
            "merged_full_track": {
                "checkpoint_json": str(merged_ready_json.resolve()),
                "ready": True,
                "matrix_status": "ready",
                "full_track_status": "ready",
                "gate_lock_status": "ready",
                "realism_gate_candidate_status": "ready",
                "generated_from_head_commit": "fixture_generated_commit",
                "merged_readiness_commit": "fixture_merged_commit",
                "validation_status": "pass",
            },
            "avx_developer_gate": {
                "summary_json": str(avx_ready_json.resolve()),
                "matrix_summary_json": str(avx_matrix_json.resolve()),
                "status": "ready",
                "physics_worse_count": 0,
                "function_better_count": 1,
                "total_profiles": 1,
            },
            "em_solver_packaging_policy": {
                "policy_json": str(em_policy_json.resolve()),
                "reference_locks_md": str(em_reference_locks_md.resolve()),
                "validator_status": "pass",
            },
            "overall_status": "ready",
        }

        ready_json = root / "closure_ready.json"
        _write_json(ready_json, base_ready)
        proc_ready = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator_script),
                "--summary-json",
                str(ready_json),
                "--require-ready",
            ],
        )
        _must_pass(proc_ready, "ready report")

        mismatch_json = root / "closure_mismatch.json"
        mismatch = copy.deepcopy(base_ready)
        mismatch["merged_full_track"]["ready"] = False
        _write_json(mismatch_json, mismatch)
        proc_mismatch = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator_script),
                "--summary-json",
                str(mismatch_json),
            ],
        )
        _must_fail(
            proc_mismatch,
            "merged-ready mismatch report",
            "merged_full_track.ready mismatch with checkpoint report",
        )

        blocked_json = root / "closure_blocked.json"
        blocked = copy.deepcopy(base_ready)
        blocked["merged_full_track"]["checkpoint_json"] = str(merged_blocked_json.resolve())
        blocked["merged_full_track"]["ready"] = False
        blocked["merged_full_track"]["validation_status"] = "fail"
        blocked["avx_developer_gate"]["summary_json"] = str(avx_blocked_json.resolve())
        blocked["avx_developer_gate"]["status"] = "blocked"
        blocked["em_solver_packaging_policy"]["validator_status"] = "fail"
        blocked["overall_status"] = "blocked"
        _write_json(blocked_json, blocked)

        proc_blocked = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator_script),
                "--summary-json",
                str(blocked_json),
            ],
        )
        _must_pass(proc_blocked, "blocked report without require-ready")

        proc_blocked_require_ready = _run(
            repo_root,
            [
                str(Path(sys.executable)),
                str(validator_script),
                "--summary-json",
                str(blocked_json),
                "--require-ready",
            ],
        )
        _must_fail(
            proc_blocked_require_ready,
            "blocked report with require-ready",
            "closure overall_status is not ready",
        )

    print("validate_run_po_sbr_operator_handoff_closure_report: pass")


if __name__ == "__main__":
    run()
