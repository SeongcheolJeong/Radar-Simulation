#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping


ALLOWED_STATUS = ("ready", "blocked", "failed")
READY_ONLY = ("ready",)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate PO-SBR local readiness regression report")
    p.add_argument("--summary-json", required=True, help="Regression summary JSON path")
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


def _assert_status(value: Any, key_name: str, allowed: tuple[str, ...]) -> str:
    status = str(value).strip()
    if status not in allowed:
        raise ValueError(f"{key_name} invalid: {status}")
    return status


def _assert_run_step(value: Any, key_name: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{key_name} must be object")
    if "ok" not in value or "return_code" not in value or "cmd" not in value:
        raise ValueError(f"{key_name} missing required keys")
    if not isinstance(value.get("cmd"), list) or len(value.get("cmd")) == 0:
        raise ValueError(f"{key_name}.cmd must be non-empty list")
    return dict(value)


def _assert_summary_json_exists(value: Any, key_name: str) -> Path:
    text = str(value).strip()
    if text == "":
        raise ValueError(f"{key_name} missing")
    path = Path(text).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{key_name} must be absolute path")
    if not path.exists():
        raise ValueError(f"{key_name} not found: {path}")
    return path


def _assert_blockers(value: Any) -> List[str]:
    if not isinstance(value, list):
        raise ValueError("blockers must be list")
    out: List[str] = []
    for idx, item in enumerate(value):
        text = str(item).strip()
        if text == "":
            raise ValueError(f"blockers[{idx}] must be non-empty string")
        out.append(text)
    return out


def _status_from_report(value: Any, key_name: str) -> str:
    if not isinstance(value, Mapping):
        raise ValueError(f"{key_name} must be object")
    return _assert_status(value.get("status"), f"{key_name}.status", ALLOWED_STATUS)


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary_json).expanduser().resolve()
    if not summary_path.exists():
        raise FileNotFoundError(f"summary report not found: {summary_path}")

    payload = _load_json(summary_path)
    if int(payload.get("version", 0)) != 1:
        raise ValueError("version must be 1")

    _assert_summary_json_exists(payload.get("full_track_bundle_summary_json"), "full_track_bundle_summary_json")
    _assert_blockers(payload.get("blockers"))

    failed_steps = payload.get("failed_steps")
    if not isinstance(failed_steps, list):
        raise ValueError("failed_steps must be list")

    reports = payload.get("reports")
    if not isinstance(reports, Mapping):
        raise ValueError("reports must be object")

    golden = reports.get("golden_path")
    if not isinstance(golden, Mapping):
        raise ValueError("reports.golden_path missing")
    _assert_summary_json_exists(golden.get("summary_json"), "reports.golden_path.summary_json")
    _assert_run_step(golden.get("run"), "reports.golden_path.run")
    _assert_run_step(golden.get("validate"), "reports.golden_path.validate")
    _status_from_report(golden, "reports.golden_path")

    kpi = reports.get("kpi_campaign")
    if not isinstance(kpi, Mapping):
        raise ValueError("reports.kpi_campaign missing")
    _assert_summary_json_exists(kpi.get("summary_json"), "reports.kpi_campaign.summary_json")
    _assert_run_step(kpi.get("run"), "reports.kpi_campaign.run")
    _assert_run_step(kpi.get("validate"), "reports.kpi_campaign.validate")
    _status_from_report(kpi, "reports.kpi_campaign")

    matrix = reports.get("kpi_scenario_matrix")
    if not isinstance(matrix, Mapping):
        raise ValueError("reports.kpi_scenario_matrix missing")
    _assert_summary_json_exists(matrix.get("summary_json"), "reports.kpi_scenario_matrix.summary_json")
    _assert_run_step(matrix.get("run"), "reports.kpi_scenario_matrix.run")
    _assert_run_step(matrix.get("validate"), "reports.kpi_scenario_matrix.validate")
    _status_from_report(matrix, "reports.kpi_scenario_matrix")

    gate_lock = reports.get("gate_lock")
    if not isinstance(gate_lock, Mapping):
        raise ValueError("reports.gate_lock missing")
    _assert_summary_json_exists(gate_lock.get("summary_json"), "reports.gate_lock.summary_json")
    _assert_summary_json_exists(gate_lock.get("stability_summary_json"), "reports.gate_lock.stability_summary_json")
    _assert_summary_json_exists(gate_lock.get("hardening_summary_json"), "reports.gate_lock.hardening_summary_json")
    _assert_run_step(gate_lock.get("run"), "reports.gate_lock.run")
    _assert_run_step(gate_lock.get("validate_gate_lock"), "reports.gate_lock.validate_gate_lock")
    _assert_run_step(gate_lock.get("validate_stability"), "reports.gate_lock.validate_stability")
    _assert_run_step(gate_lock.get("validate_hardening"), "reports.gate_lock.validate_hardening")
    _status_from_report(gate_lock, "reports.gate_lock")

    summary = payload.get("summary")
    if not isinstance(summary, Mapping):
        raise ValueError("summary must be object")
    _assert_status(summary.get("golden_path_status"), "summary.golden_path_status", ALLOWED_STATUS)
    _assert_status(summary.get("kpi_campaign_status"), "summary.kpi_campaign_status", ALLOWED_STATUS)
    _assert_status(summary.get("kpi_scenario_matrix_status"), "summary.kpi_scenario_matrix_status", ALLOWED_STATUS)
    _assert_status(summary.get("gate_lock_status"), "summary.gate_lock_status", ALLOWED_STATUS)
    overall_status = _assert_status(summary.get("overall_status"), "summary.overall_status", ALLOWED_STATUS)

    expected_status = (
        "failed"
        if len(failed_steps) > 0
        else (
            "ready"
            if str(summary.get("golden_path_status", "")).strip() == "ready"
            and str(summary.get("kpi_campaign_status", "")).strip() == "ready"
            and str(summary.get("kpi_scenario_matrix_status", "")).strip() == "ready"
            and str(summary.get("gate_lock_status", "")).strip() == "ready"
            else "blocked"
        )
    )
    if overall_status != expected_status:
        raise ValueError(f"summary.overall_status mismatch: got={overall_status}, expected={expected_status}")

    if args.require_ready and overall_status not in READY_ONLY:
        raise ValueError(f"overall_status must be ready, got: {overall_status}")

    print("validate_po_sbr_local_ready_regression_report: pass")
    print(f"  summary_json: {summary_path}")
    print(f"  overall_status: {overall_status}")
    print(f"  failed_step_count: {len(failed_steps)}")


if __name__ == "__main__":
    main()
