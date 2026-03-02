#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


def _latest(repo_root: Path, pattern: str) -> Optional[Path]:
    matches = sorted(
        (repo_root / "docs" / "reports").glob(pattern),
        key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
        reverse=True,
    )
    return matches[0].resolve() if len(matches) > 0 else None


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _run_checkpoint(
    repo_root: Path,
    env: dict,
    run_id_date: str,
) -> tuple[str, Path, dict]:
    proc = subprocess.run(
        ["bash", "scripts/run_po_sbr_myproject_readiness_checkpoint.sh", run_id_date],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            "run_po_sbr_myproject_readiness_checkpoint.sh failed\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}\n"
        )

    combined_out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    m = re.search(r"checkpoint_json=(.+)$", combined_out, flags=re.MULTILINE)
    if not m:
        raise AssertionError(f"checkpoint_json line not found in output:\n{combined_out}")
    checkpoint_path = Path(m.group(1).strip())
    if not checkpoint_path.is_absolute():
        checkpoint_path = (repo_root / checkpoint_path).resolve()
    else:
        checkpoint_path = checkpoint_path.resolve()
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"checkpoint report missing: {checkpoint_path}")

    payload = _load_json(checkpoint_path)
    return combined_out, checkpoint_path, payload


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    function_test = _latest(repo_root, "po_sbr_physical_full_track_function_test_*.json")
    local_ready = _latest(repo_root, "po_sbr_local_ready_regression_*.json")
    avx_gate = _latest(repo_root, "po_sbr_avx_developer_gate_*.json")
    baseline_manifest = (
        repo_root
        / "docs"
        / "reports"
        / "baselines"
        / "po_sbr_local_ready_2026_03_01_pc_self"
        / "baseline_manifest.json"
    ).resolve()

    if function_test is None:
        raise FileNotFoundError("missing function-test report under docs/reports")
    if local_ready is None:
        raise FileNotFoundError("missing local-ready regression report under docs/reports")
    if avx_gate is None:
        raise FileNotFoundError("missing AVX developer gate report under docs/reports")
    if not baseline_manifest.exists():
        raise FileNotFoundError(f"missing baseline manifest: {baseline_manifest}")

    avx_payload = _load_json(avx_gate)
    avx_matrix = Path(str(avx_payload.get("matrix_report_summary", {}).get("path", "")).strip()).expanduser()
    if not avx_matrix.is_absolute():
        avx_matrix = (repo_root / avx_matrix).resolve()
    else:
        avx_matrix = avx_matrix.resolve()
    if not avx_matrix.exists():
        raise FileNotFoundError(f"missing AVX gate matrix summary: {avx_matrix}")

    env = dict(os.environ)
    env["PO_SBR_FUNCTION_TEST_JSON_OVERRIDE"] = str(function_test)
    env["PO_SBR_LOCAL_READY_SUMMARY_JSON_OVERRIDE"] = str(local_ready)
    env["PO_SBR_BASELINE_MANIFEST_JSON_OVERRIDE"] = str(baseline_manifest)
    env["PO_SBR_AVX_DEVELOPER_GATE_SUMMARY_JSON_OVERRIDE"] = str(avx_gate)
    env["PO_SBR_AVX_DEVELOPER_GATE_MATRIX_SUMMARY_JSON_OVERRIDE"] = str(avx_matrix)

    run_id_date_default = "2026_03_02_default"
    run_id_date_skip = "2026_03_02_skip"
    combined_out_default, checkpoint_path_default, payload_default = _run_checkpoint(
        repo_root=repo_root,
        env=env,
        run_id_date=run_id_date_default,
    )
    if "validate post-change deterministic gate" not in combined_out_default:
        raise AssertionError(
            "post-change deterministic validator step missing from default checkpoint output:\n"
            f"{combined_out_default}"
        )
    if "validate operator-closure report deterministic runner" not in combined_out_default:
        raise AssertionError(
            "operator-closure report deterministic validator step missing from default checkpoint output:\n"
            f"{combined_out_default}"
        )
    if "validate_run_po_sbr_operator_handoff_closure_report: pass" not in combined_out_default:
        raise AssertionError(
            "operator-closure report deterministic validator pass marker missing from default checkpoint output:\n"
            f"{combined_out_default}"
        )
    if "validate progress snapshot deterministic runner" not in combined_out_default:
        raise AssertionError(
            "progress snapshot deterministic validator step missing from default checkpoint output:\n"
            f"{combined_out_default}"
        )
    if "validate pre-push local-artifact mode" not in combined_out_default:
        raise AssertionError(
            "pre-push local-artifact validator step missing from default checkpoint output:\n"
            f"{combined_out_default}"
        )
    if "validate EM solver packaging policy" not in combined_out_default:
        raise AssertionError(
            "EM solver packaging policy validator step missing from default checkpoint output:\n"
            f"{combined_out_default}"
        )
    if "validate_em_solver_packaging_policy: pass" not in combined_out_default:
        raise AssertionError(
            "EM solver packaging policy pass marker missing from default checkpoint output:\n"
            f"{combined_out_default}"
        )
    if "validate myproject checkpoint report" not in combined_out_default:
        raise AssertionError(
            "myproject checkpoint report validator step missing from default checkpoint output:\n"
            f"{combined_out_default}"
        )
    if "validate_po_sbr_myproject_readiness_checkpoint_report: pass" not in combined_out_default:
        raise AssertionError(
            "myproject checkpoint report pass marker missing from default checkpoint output:\n"
            f"{combined_out_default}"
        )
    if "hook_skip_mode_matrix_verified: true" not in combined_out_default:
        raise AssertionError(
            "pre-push selftest matrix marker missing from default checkpoint output:\n"
            f"{combined_out_default}"
        )
    if "hook_closure_report_skip_only_verified: true" not in combined_out_default:
        raise AssertionError(
            "pre-push closure-report-skip-only marker missing from default checkpoint output:\n"
            f"{combined_out_default}"
        )
    if "tracked_report_changes: 0" not in combined_out_default:
        raise AssertionError(
            "pre-push selftest tracked-report marker missing from default checkpoint output:\n"
            f"{combined_out_default}"
        )
    assert payload_default.get("report_name") == "po_sbr_myproject_readiness_checkpoint", payload_default.get(
        "report_name"
    )
    assert int(payload_default.get("version", 0)) == 1, payload_default.get("version")
    run_id_default = str(payload_default.get("run_id", "")).strip()
    assert run_id_default != "", payload_default.get("run_id")
    run_id_default_tail = run_id_default.rsplit("_", 1)[-1]
    head_commit_default = str(payload_default.get("head_commit", "")).strip()
    if not head_commit_default.startswith(run_id_default_tail):
        raise AssertionError(
            "default head_commit does not start with run_id tail:\n"
            f"run_id={run_id_default}\n"
            f"head_commit={head_commit_default}"
        )
    assert payload_default.get("overall_status") == "ready", payload_default.get("overall_status")
    assert payload_default.get("avx_developer_gate_status") == "ready", payload_default.get(
        "avx_developer_gate_status"
    )
    assert payload_default.get("em_policy_validator_status") == "pass", payload_default.get(
        "em_policy_validator_status"
    )
    assert payload_default.get("function_test_overall_status") == "ready", payload_default.get(
        "function_test_overall_status"
    )
    assert payload_default.get("local_ready_overall_status") == "ready", payload_default.get(
        "local_ready_overall_status"
    )
    assert payload_default.get("baseline_drift_verdict") == "match", payload_default.get(
        "baseline_drift_verdict"
    )
    assert int(payload_default.get("baseline_drift_difference_count", -1)) == 0, payload_default.get(
        "baseline_drift_difference_count"
    )
    assert payload_default.get("post_change_gate_validator_status") == "pass", payload_default.get(
        "post_change_gate_validator_status"
    )
    assert payload_default.get("closure_report_validator_status") == "pass", payload_default.get(
        "closure_report_validator_status"
    )
    assert bool(payload_default.get("progress_snapshot_overall_ready", False)) is True
    assert payload_default.get("progress_snapshot_validator_status") == "pass", payload_default.get(
        "progress_snapshot_validator_status"
    )
    assert payload_default.get("hook_selftest_validator_status") == "pass", payload_default.get(
        "hook_selftest_validator_status"
    )
    checks_default = payload_default.get("checkpoint_checks")
    if not isinstance(checks_default, dict):
        raise AssertionError("checkpoint_checks missing or not an object in default branch payload")
    for key in (
        "function_test_ready",
        "local_ready_ready",
        "baseline_drift_match",
        "avx_developer_gate_ready",
        "em_policy_validator_ok",
        "post_change_gate_validator_ok",
        "closure_report_validator_ok",
        "progress_snapshot_overall_ready",
        "progress_snapshot_validator_ok",
        "hook_selftest_validator_ok",
    ):
        if not bool(checks_default.get(key, False)):
            raise AssertionError(f"default checkpoint_checks[{key}] is not true")

    env_skip = dict(env)
    env_skip["PO_SBR_SKIP_POST_CHANGE_GATE_VALIDATOR"] = "1"
    env_skip["PO_SBR_SKIP_PROGRESS_SNAPSHOT_VALIDATOR"] = "1"
    env_skip["PO_SBR_SKIP_HOOK_SELFTEST"] = "1"
    env_skip["PO_SBR_SKIP_EM_POLICY_VALIDATOR"] = "1"
    env_skip["PO_SBR_SKIP_CLOSURE_REPORT_VALIDATOR"] = "1"
    combined_out_skip, checkpoint_path_skip, payload_skip = _run_checkpoint(
        repo_root=repo_root,
        env=env_skip,
        run_id_date=run_id_date_skip,
    )
    if "skip post-change deterministic validator (PO_SBR_SKIP_POST_CHANGE_GATE_VALIDATOR=1)" not in combined_out_skip:
        raise AssertionError(
            "post-change deterministic skip log line missing from checkpoint output:\n"
            f"{combined_out_skip}"
        )
    if "skip progress snapshot deterministic validator (PO_SBR_SKIP_PROGRESS_SNAPSHOT_VALIDATOR=1)" not in combined_out_skip:
        raise AssertionError(
            "progress snapshot deterministic skip log line missing from checkpoint output:\n"
            f"{combined_out_skip}"
        )
    if "skip pre-push local-artifact validator (PO_SBR_SKIP_HOOK_SELFTEST=1)" not in combined_out_skip:
        raise AssertionError(
            "pre-push local-artifact skip log line missing from checkpoint output:\n"
            f"{combined_out_skip}"
        )
    if "skip operator-closure report deterministic validator (PO_SBR_SKIP_CLOSURE_REPORT_VALIDATOR=1)" not in combined_out_skip:
        raise AssertionError(
            "operator-closure report deterministic validator skip log line missing from checkpoint output:\n"
            f"{combined_out_skip}"
        )
    if "validate_run_po_sbr_operator_handoff_closure_report: pass" in combined_out_skip:
        raise AssertionError(
            "operator-closure report deterministic validator pass marker unexpectedly present in skip checkpoint output:\n"
            f"{combined_out_skip}"
        )
    if "skip EM solver packaging policy validator (PO_SBR_SKIP_EM_POLICY_VALIDATOR=1)" not in combined_out_skip:
        raise AssertionError(
            "EM solver packaging policy skip log line missing from checkpoint output:\n"
            f"{combined_out_skip}"
        )
    if "validate myproject checkpoint report" not in combined_out_skip:
        raise AssertionError(
            "myproject checkpoint report validator step missing from skip checkpoint output:\n"
            f"{combined_out_skip}"
        )
    if "validate_po_sbr_myproject_readiness_checkpoint_report: pass" not in combined_out_skip:
        raise AssertionError(
            "myproject checkpoint report pass marker missing from skip checkpoint output:\n"
            f"{combined_out_skip}"
        )
    if "hook_skip_mode_matrix_verified: true" in combined_out_skip:
        raise AssertionError(
            "pre-push selftest matrix marker unexpectedly present in hook-selftest-skip branch:\n"
            f"{combined_out_skip}"
        )
    if "hook_closure_report_skip_only_verified: true" in combined_out_skip:
        raise AssertionError(
            "pre-push closure-report-skip-only marker unexpectedly present in hook-selftest-skip branch:\n"
            f"{combined_out_skip}"
        )
    assert payload_skip.get("report_name") == "po_sbr_myproject_readiness_checkpoint", payload_skip.get(
        "report_name"
    )
    assert int(payload_skip.get("version", 0)) == 1, payload_skip.get("version")
    run_id_skip = str(payload_skip.get("run_id", "")).strip()
    assert run_id_skip != "", payload_skip.get("run_id")
    run_id_skip_tail = run_id_skip.rsplit("_", 1)[-1]
    head_commit_skip = str(payload_skip.get("head_commit", "")).strip()
    if not head_commit_skip.startswith(run_id_skip_tail):
        raise AssertionError(
            "skip head_commit does not start with run_id tail:\n"
            f"run_id={run_id_skip}\n"
            f"head_commit={head_commit_skip}"
        )
    assert payload_skip.get("overall_status") == "ready", payload_skip.get("overall_status")
    assert payload_skip.get("avx_developer_gate_status") == "ready", payload_skip.get("avx_developer_gate_status")
    assert payload_skip.get("em_policy_validator_status") == "skipped", payload_skip.get(
        "em_policy_validator_status"
    )
    assert payload_skip.get("function_test_overall_status") == "ready", payload_skip.get(
        "function_test_overall_status"
    )
    assert payload_skip.get("local_ready_overall_status") == "ready", payload_skip.get(
        "local_ready_overall_status"
    )
    assert payload_skip.get("baseline_drift_verdict") == "match", payload_skip.get("baseline_drift_verdict")
    assert int(payload_skip.get("baseline_drift_difference_count", -1)) == 0, payload_skip.get(
        "baseline_drift_difference_count"
    )
    assert payload_skip.get("post_change_gate_validator_status") == "skipped", payload_skip.get(
        "post_change_gate_validator_status"
    )
    assert payload_skip.get("closure_report_validator_status") == "skipped", payload_skip.get(
        "closure_report_validator_status"
    )
    assert bool(payload_skip.get("progress_snapshot_overall_ready", False)) is True
    assert payload_skip.get("progress_snapshot_validator_status") == "skipped", payload_skip.get(
        "progress_snapshot_validator_status"
    )
    assert payload_skip.get("hook_selftest_validator_status") == "skipped", payload_skip.get(
        "hook_selftest_validator_status"
    )
    checks_skip = payload_skip.get("checkpoint_checks")
    if not isinstance(checks_skip, dict):
        raise AssertionError("checkpoint_checks missing or not an object in skip branch payload")
    for key in (
        "function_test_ready",
        "local_ready_ready",
        "baseline_drift_match",
        "avx_developer_gate_ready",
        "em_policy_validator_ok",
        "post_change_gate_validator_ok",
        "closure_report_validator_ok",
        "progress_snapshot_overall_ready",
        "progress_snapshot_validator_ok",
        "hook_selftest_validator_ok",
    ):
        if not bool(checks_skip.get(key, False)):
            raise AssertionError(f"skip checkpoint_checks[{key}] is not true")
    if checkpoint_path_default == checkpoint_path_skip:
        raise AssertionError(
            "default and skip checkpoint paths must differ to avoid overwrite masking:\n"
            f"default={checkpoint_path_default}\n"
            f"skip={checkpoint_path_skip}"
        )

    progress_json_default = Path(str(payload_default.get("progress_snapshot_json", "")).strip()).expanduser().resolve()
    progress_json_skip = Path(str(payload_skip.get("progress_snapshot_json", "")).strip()).expanduser().resolve()
    if not progress_json_default.exists():
        raise FileNotFoundError(f"default progress snapshot missing: {progress_json_default}")
    if not progress_json_skip.exists():
        raise FileNotFoundError(f"skip progress snapshot missing: {progress_json_skip}")
    progress_default_payload = _load_json(progress_json_default)
    progress_skip_payload = _load_json(progress_json_skip)
    if run_id_default not in progress_json_default.name:
        raise AssertionError(
            "default progress snapshot filename does not include run_id:\n"
            f"run_id={run_id_default}\n"
            f"file={progress_json_default.name}"
        )
    if run_id_skip not in progress_json_skip.name:
        raise AssertionError(
            "skip progress snapshot filename does not include run_id:\n"
            f"run_id={run_id_skip}\n"
            f"file={progress_json_skip.name}"
        )
    if not bool(progress_default_payload.get("overall_ready", False)):
        raise AssertionError(f"default progress snapshot overall_ready is not true: {progress_json_default}")
    if not bool(progress_skip_payload.get("overall_ready", False)):
        raise AssertionError(f"skip progress snapshot overall_ready is not true: {progress_json_skip}")
    if progress_json_default == progress_json_skip:
        raise AssertionError(
            "default and skip progress snapshot paths must differ to avoid overwrite masking:\n"
            f"default={progress_json_default}\n"
            f"skip={progress_json_skip}"
        )

    avx_gate_path = Path(str(payload_skip.get("avx_developer_gate_summary_json", "")).strip()).expanduser().resolve()
    avx_matrix_path = (
        Path(str(payload_skip.get("avx_developer_gate_matrix_summary_json", "")).strip())
        .expanduser()
        .resolve()
    )
    drift_default = Path(str(payload_default.get("baseline_drift_report_json", "")).strip()).expanduser().resolve()
    drift_skip = Path(str(payload_skip.get("baseline_drift_report_json", "")).strip()).expanduser().resolve()
    if run_id_default not in drift_default.name:
        raise AssertionError(
            "default baseline drift filename does not include run_id:\n"
            f"run_id={run_id_default}\n"
            f"file={drift_default.name}"
        )
    if run_id_skip not in drift_skip.name:
        raise AssertionError(
            "skip baseline drift filename does not include run_id:\n"
            f"run_id={run_id_skip}\n"
            f"file={drift_skip.name}"
        )
    if not avx_gate_path.exists():
        raise FileNotFoundError(f"checkpoint avx gate summary missing: {avx_gate_path}")
    if not avx_matrix_path.exists():
        raise FileNotFoundError(f"checkpoint avx matrix summary missing: {avx_matrix_path}")
    em_policy_path = Path(
        str(payload_skip.get("em_solver_policy_json", "")).strip()
    ).expanduser().resolve()
    em_reference_locks_path = Path(
        str(payload_skip.get("em_solver_reference_locks_md", "")).strip()
    ).expanduser().resolve()
    if not em_policy_path.exists():
        raise FileNotFoundError(f"checkpoint EM policy json missing: {em_policy_path}")
    if not em_reference_locks_path.exists():
        raise FileNotFoundError(
            f"checkpoint EM reference-locks markdown missing: {em_reference_locks_path}"
        )

    print("validate_run_po_sbr_myproject_readiness_checkpoint: pass")
    print(f"  checkpoint_json_default: {checkpoint_path_default}")
    print(f"  checkpoint_json_skip: {checkpoint_path_skip}")
    print(f"  progress_snapshot_json_default: {progress_json_default}")
    print(f"  progress_snapshot_json_skip: {progress_json_skip}")
    print(f"  avx_developer_gate_summary_json: {avx_gate_path}")
    print(f"  avx_developer_gate_matrix_summary_json: {avx_matrix_path}")
    print(f"  em_solver_policy_json: {em_policy_path}")
    print(f"  em_solver_reference_locks_md: {em_reference_locks_path}")


if __name__ == "__main__":
    run()
