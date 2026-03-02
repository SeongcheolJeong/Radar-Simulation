#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, Mapping


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Validate PO-SBR operator handoff closure report"
    )
    p.add_argument("--summary-json", required=True, help="Closure summary JSON path")
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


def _require_mapping(value: Any, key: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be object")
    return value


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


def _require_nonnegative_int(value: Any, key: str) -> int:
    try:
        ivalue = int(value)
    except Exception as exc:
        raise ValueError(f"{key} must be integer") from exc
    if ivalue < 0:
        raise ValueError(f"{key} must be >= 0")
    return ivalue


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary_json).expanduser().resolve()
    if not summary_path.exists():
        raise FileNotFoundError(f"summary json not found: {summary_path}")

    payload = _load_json(summary_path)
    report_name = str(payload.get("report_name", "")).strip()
    if report_name != "po_sbr_operator_handoff_closure":
        raise ValueError(f"report_name invalid: {report_name}")

    _nonempty_text(payload.get("generated_at_utc"), "generated_at_utc")
    workspace_root = _nonempty_text(payload.get("workspace_root"), "workspace_root")
    if not Path(workspace_root).expanduser().is_absolute():
        raise ValueError("workspace_root must be absolute path")
    _nonempty_text(payload.get("branch"), "branch")
    _nonempty_text(payload.get("head_commit"), "head_commit")

    frontend = _require_mapping(
        payload.get("frontend_timeline_import_audit"),
        "frontend_timeline_import_audit",
    )
    milestones = frontend.get("milestones")
    if not isinstance(milestones, list) or len(milestones) == 0:
        raise ValueError("frontend_timeline_import_audit.milestones must be non-empty list")
    for idx, milestone in enumerate(milestones):
        if str(milestone).strip() == "":
            raise ValueError(f"frontend_timeline_import_audit.milestones[{idx}] missing")
    frontend_validator_status = _status(
        frontend.get("validator_status"),
        "frontend_timeline_import_audit.validator_status",
        ("pass", "fail"),
    )
    frontend_api_status = _status(
        frontend.get("api_regression_status"),
        "frontend_timeline_import_audit.api_regression_status",
        ("pass", "skipped", "fail"),
    )

    merged = _require_mapping(payload.get("merged_full_track"), "merged_full_track")
    checkpoint_json = _require_abs_existing_path(
        merged.get("checkpoint_json"),
        "merged_full_track.checkpoint_json",
    )
    merged_ready = _require_bool(merged.get("ready"), "merged_full_track.ready")
    merged_validation_status = _status(
        merged.get("validation_status"),
        "merged_full_track.validation_status",
        ("pass", "skipped", "fail"),
    )
    _status(
        merged.get("matrix_status"),
        "merged_full_track.matrix_status",
        ("ready", "blocked", "failed"),
    )
    _status(
        merged.get("full_track_status"),
        "merged_full_track.full_track_status",
        ("ready", "blocked", "failed"),
    )
    _status(
        merged.get("gate_lock_status"),
        "merged_full_track.gate_lock_status",
        ("ready", "blocked", "failed"),
    )
    _status(
        merged.get("realism_gate_candidate_status"),
        "merged_full_track.realism_gate_candidate_status",
        ("ready", "blocked", "failed"),
    )
    _nonempty_text(
        merged.get("generated_from_head_commit"),
        "merged_full_track.generated_from_head_commit",
    )
    _nonempty_text(
        merged.get("merged_readiness_commit"),
        "merged_full_track.merged_readiness_commit",
    )

    avx = _require_mapping(payload.get("avx_developer_gate"), "avx_developer_gate")
    avx_summary_json = _require_abs_existing_path(
        avx.get("summary_json"), "avx_developer_gate.summary_json"
    )
    _require_abs_existing_path(
        avx.get("matrix_summary_json"),
        "avx_developer_gate.matrix_summary_json",
    )
    avx_status = _status(
        avx.get("status"),
        "avx_developer_gate.status",
        ("ready", "blocked"),
    )
    _require_nonnegative_int(
        avx.get("physics_worse_count"), "avx_developer_gate.physics_worse_count"
    )
    _require_nonnegative_int(
        avx.get("function_better_count"), "avx_developer_gate.function_better_count"
    )
    _require_nonnegative_int(
        avx.get("total_profiles"), "avx_developer_gate.total_profiles"
    )

    em = _require_mapping(
        payload.get("em_solver_packaging_policy"),
        "em_solver_packaging_policy",
    )
    _require_abs_existing_path(
        em.get("policy_json"),
        "em_solver_packaging_policy.policy_json",
    )
    _require_abs_existing_path(
        em.get("reference_locks_md"),
        "em_solver_packaging_policy.reference_locks_md",
    )
    em_validator_status = _status(
        em.get("validator_status"),
        "em_solver_packaging_policy.validator_status",
        ("pass", "skipped", "fail"),
    )

    checkpoint_payload = _load_json(checkpoint_json)
    checkpoint_ready_ref = bool(checkpoint_payload.get("ready", False))
    if merged_ready != checkpoint_ready_ref:
        raise ValueError("merged_full_track.ready mismatch with checkpoint report")

    avx_payload = _load_json(avx_summary_json)
    avx_status_ref = _status(
        avx_payload.get("developer_gate_status"),
        "avx_report.developer_gate_status",
        ("ready", "blocked"),
    )
    if avx_status != avx_status_ref:
        raise ValueError("avx_developer_gate.status mismatch with AVX gate report")

    expected_overall_status = (
        "ready"
        if (
            frontend_validator_status == "pass"
            and frontend_api_status in {"pass", "skipped"}
            and merged_ready
            and merged_validation_status in {"pass", "skipped"}
            and avx_status == "ready"
            and em_validator_status in {"pass", "skipped"}
        )
        else "blocked"
    )
    overall_status = _status(
        payload.get("overall_status"),
        "overall_status",
        ("ready", "blocked"),
    )
    if overall_status != expected_overall_status:
        raise ValueError(
            "overall_status mismatch with computed closure policy: "
            f"expected={expected_overall_status}, actual={overall_status}"
        )
    if bool(args.require_ready) and overall_status != "ready":
        raise SystemExit("closure overall_status is not ready")

    print("validate_po_sbr_operator_handoff_closure_report: pass")
    print(f"  summary_json: {summary_path}")
    print(f"  overall_status: {overall_status}")
    print(f"  merged_checkpoint_json: {checkpoint_json}")
    print(f"  avx_summary_json: {avx_summary_json}")


if __name__ == "__main__":
    main()
