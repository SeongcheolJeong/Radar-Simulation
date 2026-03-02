#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, Mapping


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Validate PO-SBR myproject readiness checkpoint report"
    )
    p.add_argument("--summary-json", required=True, help="Checkpoint summary JSON path")
    p.add_argument(
        "--require-ready",
        action="store_true",
        help="Fail validation unless overall_status=ready",
    )
    return p.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("summary json must be object")
    return payload


def _status(value: Any, key: str, allowed: tuple[str, ...]) -> str:
    text = str(value).strip()
    if text not in allowed:
        raise ValueError(f"{key} invalid: {text}")
    return text


def _nonempty_text(value: Any, key: str) -> str:
    text = str(value).strip()
    if text == "":
        raise ValueError(f"{key} missing")
    return text


def _require_abs_existing_path(value: Any, key: str) -> Path:
    text = str(value).strip()
    if text == "":
        raise ValueError(f"{key} missing")
    path = Path(text).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{key} must be absolute path")
    if not path.exists():
        raise ValueError(f"{key} not found: {path}")
    return path


def _require_bool(value: Any, key: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be boolean")
    return value


def _require_checks(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("checkpoint_checks must be object")
    required = (
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
    )
    for key in required:
        if key not in value:
            raise ValueError(f"checkpoint_checks.{key} missing")
        if not isinstance(value.get(key), bool):
            raise ValueError(f"checkpoint_checks.{key} must be boolean")
    return value


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary_json).expanduser().resolve()
    if not summary_path.exists():
        raise FileNotFoundError(f"summary json not found: {summary_path}")

    payload = _load_json(summary_path)
    version = int(payload.get("version", 0))
    if version != 1:
        raise ValueError(f"version must be 1, got: {version}")

    report_name = str(payload.get("report_name", "")).strip()
    if report_name != "po_sbr_myproject_readiness_checkpoint":
        raise ValueError(f"report_name invalid: {report_name}")
    _nonempty_text(payload.get("generated_at_utc"), "generated_at_utc")
    workspace_root = _nonempty_text(payload.get("workspace_root"), "workspace_root")
    workspace_root_path = Path(workspace_root).expanduser()
    if not workspace_root_path.is_absolute():
        raise ValueError("workspace_root must be absolute path")
    run_id = _nonempty_text(payload.get("run_id"), "run_id")
    _nonempty_text(payload.get("branch"), "branch")
    head_commit = _nonempty_text(payload.get("head_commit"), "head_commit")
    run_id_tail = run_id.rsplit("_", 1)[-1]
    if run_id_tail == "":
        raise ValueError("run_id tail must be non-empty")
    if not head_commit.startswith(run_id_tail):
        raise ValueError(
            "head_commit must start with run_id tail: "
            f"tail={run_id_tail}, head_commit={head_commit}"
        )

    function_test_summary_json = _require_abs_existing_path(
        payload.get("function_test_summary_json"), "function_test_summary_json"
    )
    _require_abs_existing_path(payload.get("bundle_summary_json"), "bundle_summary_json")
    _require_abs_existing_path(payload.get("gate_lock_summary_json"), "gate_lock_summary_json")
    local_ready_summary_json = _require_abs_existing_path(
        payload.get("local_ready_summary_json"), "local_ready_summary_json"
    )
    _require_abs_existing_path(payload.get("baseline_manifest_json"), "baseline_manifest_json")
    baseline_drift_report_json = _require_abs_existing_path(
        payload.get("baseline_drift_report_json"), "baseline_drift_report_json"
    )
    avx_developer_gate_summary_json = _require_abs_existing_path(
        payload.get("avx_developer_gate_summary_json"),
        "avx_developer_gate_summary_json",
    )
    _require_abs_existing_path(
        payload.get("em_solver_policy_json"),
        "em_solver_policy_json",
    )
    _require_abs_existing_path(
        payload.get("em_solver_reference_locks_md"),
        "em_solver_reference_locks_md",
    )
    _require_abs_existing_path(
        payload.get("avx_developer_gate_matrix_summary_json"),
        "avx_developer_gate_matrix_summary_json",
    )
    progress_snapshot_json = _require_abs_existing_path(
        payload.get("progress_snapshot_json"),
        "progress_snapshot_json",
    )
    if run_id not in baseline_drift_report_json.name:
        raise ValueError(
            "baseline_drift_report_json filename must include run_id: "
            f"run_id={run_id}, file={baseline_drift_report_json.name}"
        )
    if run_id not in progress_snapshot_json.name:
        raise ValueError(
            "progress_snapshot_json filename must include run_id: "
            f"run_id={run_id}, file={progress_snapshot_json.name}"
        )

    function_test_payload = _load_json(function_test_summary_json)
    local_ready_payload = _load_json(local_ready_summary_json)
    baseline_drift_payload = _load_json(baseline_drift_report_json)
    avx_gate_payload = _load_json(avx_developer_gate_summary_json)
    progress_snapshot_payload = _load_json(progress_snapshot_json)

    function_test_status_ref = _status(
        function_test_payload.get("overall_status"),
        "function_test_report.overall_status",
        ("ready", "blocked", "failed"),
    )
    local_ready_summary_ref = local_ready_payload.get("summary")
    if isinstance(local_ready_summary_ref, Mapping):
        local_ready_status_ref = _status(
            local_ready_summary_ref.get("overall_status"),
            "local_ready_report.summary.overall_status",
            ("ready", "blocked", "failed"),
        )
    else:
        local_ready_status_ref = _status(
            local_ready_payload.get("overall_status"),
            "local_ready_report.overall_status",
            ("ready", "blocked", "failed"),
        )
    baseline_drift_verdict_ref = _status(
        baseline_drift_payload.get("drift_verdict"),
        "baseline_drift_report.drift_verdict",
        ("match", "mismatch"),
    )
    baseline_drift_difference_count_ref = int(
        baseline_drift_payload.get("difference_count", -1)
    )
    if baseline_drift_difference_count_ref < 0:
        raise ValueError("baseline_drift_report.difference_count must be >= 0")
    avx_status_ref = _status(
        avx_gate_payload.get("developer_gate_status"),
        "avx_developer_gate_report.developer_gate_status",
        ("ready", "blocked"),
    )
    progress_snapshot_overall_ready_ref = _require_bool(
        progress_snapshot_payload.get("overall_ready"),
        "progress_snapshot_report.overall_ready",
    )

    function_test_status = _status(
        payload.get("function_test_overall_status"),
        "function_test_overall_status",
        ("ready", "blocked", "failed"),
    )
    local_ready_status = _status(
        payload.get("local_ready_overall_status"),
        "local_ready_overall_status",
        ("ready", "blocked", "failed"),
    )
    avx_status = _status(
        payload.get("avx_developer_gate_status"),
        "avx_developer_gate_status",
        ("ready", "blocked"),
    )
    em_policy_validator_status = _status(
        payload.get("em_policy_validator_status"),
        "em_policy_validator_status",
        ("pass", "skipped", "fail"),
    )
    post_change_validator_status = _status(
        payload.get("post_change_gate_validator_status"),
        "post_change_gate_validator_status",
        ("pass", "skipped", "fail"),
    )
    closure_report_validator_status = _status(
        payload.get("closure_report_validator_status"),
        "closure_report_validator_status",
        ("pass", "skipped", "fail"),
    )
    progress_validator_status = _status(
        payload.get("progress_snapshot_validator_status"),
        "progress_snapshot_validator_status",
        ("pass", "skipped", "fail"),
    )
    hook_validator_status = _status(
        payload.get("hook_selftest_validator_status"),
        "hook_selftest_validator_status",
        ("pass", "skipped", "fail"),
    )
    baseline_drift_verdict = _status(
        payload.get("baseline_drift_verdict"),
        "baseline_drift_verdict",
        ("match", "mismatch"),
    )

    baseline_drift_difference_count = int(payload.get("baseline_drift_difference_count", -1))
    if baseline_drift_difference_count < 0:
        raise ValueError("baseline_drift_difference_count must be >= 0")

    progress_snapshot_overall_ready = _require_bool(
        payload.get("progress_snapshot_overall_ready"),
        "progress_snapshot_overall_ready",
    )
    if function_test_status != function_test_status_ref:
        raise ValueError("function_test_overall_status mismatch with function-test report")
    if local_ready_status != local_ready_status_ref:
        raise ValueError("local_ready_overall_status mismatch with local-ready report")
    if baseline_drift_verdict != baseline_drift_verdict_ref:
        raise ValueError("baseline_drift_verdict mismatch with baseline-drift report")
    if baseline_drift_difference_count != baseline_drift_difference_count_ref:
        raise ValueError(
            "baseline_drift_difference_count mismatch with baseline-drift report"
        )
    if avx_status != avx_status_ref:
        raise ValueError("avx_developer_gate_status mismatch with AVX gate report")
    if progress_snapshot_overall_ready != progress_snapshot_overall_ready_ref:
        raise ValueError(
            "progress_snapshot_overall_ready mismatch with progress-snapshot report"
        )

    checks = _require_checks(payload.get("checkpoint_checks"))
    expected_checks = {
        "function_test_ready": function_test_status_ref == "ready",
        "local_ready_ready": local_ready_status_ref == "ready",
        "baseline_drift_match": (
            baseline_drift_verdict_ref == "match"
            and baseline_drift_difference_count_ref == 0
        ),
        "avx_developer_gate_ready": avx_status_ref == "ready",
        "em_policy_validator_ok": em_policy_validator_status in {"pass", "skipped"},
        "post_change_gate_validator_ok": post_change_validator_status in {"pass", "skipped"},
        "closure_report_validator_ok": closure_report_validator_status in {"pass", "skipped"},
        "progress_snapshot_overall_ready": progress_snapshot_overall_ready_ref,
        "progress_snapshot_validator_ok": progress_validator_status in {"pass", "skipped"},
        "hook_selftest_validator_ok": hook_validator_status in {"pass", "skipped"},
    }
    for key, expected in expected_checks.items():
        actual = bool(checks.get(key, False))
        if actual != expected:
            raise ValueError(
                f"checkpoint_checks.{key} mismatch: actual={actual}, expected={expected}"
            )

    expected_overall = "ready" if all(expected_checks.values()) else "blocked"
    overall_status = _status(payload.get("overall_status"), "overall_status", ("ready", "blocked"))
    if overall_status != expected_overall:
        raise ValueError(
            f"overall_status mismatch: got={overall_status}, expected={expected_overall}"
        )

    if args.require_ready and overall_status != "ready":
        raise ValueError(f"overall_status must be ready, got: {overall_status}")

    print("validate_po_sbr_myproject_readiness_checkpoint_report: pass")
    print(f"  summary_json: {summary_path}")
    print(f"  version: {version}")
    print(f"  overall_status: {overall_status}")
    print(f"  function_test_overall_status: {function_test_status}")
    print(f"  local_ready_overall_status: {local_ready_status}")
    print(f"  baseline_drift_verdict: {baseline_drift_verdict}")
    print(f"  baseline_drift_difference_count: {baseline_drift_difference_count}")
    print(f"  avx_developer_gate_status: {avx_status}")
    print(f"  em_policy_validator_status: {em_policy_validator_status}")
    print(f"  closure_report_validator_status: {closure_report_validator_status}")
    print(f"  progress_snapshot_overall_ready: {progress_snapshot_overall_ready}")


if __name__ == "__main__":
    main()
