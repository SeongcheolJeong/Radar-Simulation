#!/usr/bin/env python3
"""Validate RadarSimPy readiness checkpoint report contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Mapping


REQUIRED_CHECK_KEYS = (
    "smoke_gate_pass",
    "wrapper_gate_pass",
    "progress_snapshot_generated",
    "progress_integration_stage_ready",
    "progress_wrapper_stage_ready",
    "function_api_stage_ready",
    "migration_stage_ready",
    "real_e2e_stage_ready",
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Validate radarsimpy_readiness_checkpoint report JSON."
    )
    p.add_argument("--summary-json", required=True)
    p.add_argument("--require-ready", action="store_true")
    return p.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _require_str(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"{key} must be non-empty string")
    return value


def _require_bool(payload: Mapping[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be bool")
    return bool(value)


def _require_abs_existing_path(path_value: Any, field_name: str, *, optional: bool = False) -> str:
    text = str(path_value or "").strip()
    if text == "":
        if optional:
            return ""
        raise ValueError(f"{field_name} must be non-empty path")
    p = Path(text).expanduser().resolve()
    if not p.is_absolute():
        raise ValueError(f"{field_name} must be absolute path: {p}")
    if not p.exists():
        raise ValueError(f"{field_name} path does not exist: {p}")
    return str(p)


def _validate_command_block(payload: Mapping[str, Any], key: str, *, allow_skipped: bool = False) -> None:
    row = payload.get(key)
    if not isinstance(row, Mapping):
        raise ValueError(f"commands.{key} must be object")
    if allow_skipped and bool(row.get("skipped", False)):
        return
    rc = row.get("returncode")
    ok = row.get("pass")
    if not isinstance(rc, int):
        raise ValueError(f"commands.{key}.returncode must be int")
    if not isinstance(ok, bool):
        raise ValueError(f"commands.{key}.pass must be bool")


def main() -> None:
    args = parse_args()
    summary_json = Path(args.summary_json).expanduser().resolve()
    payload = _load_json(summary_json)

    report_name = _require_str(payload, "report_name")
    if report_name != "radarsimpy_readiness_checkpoint":
        raise ValueError(f"report_name must be radarsimpy_readiness_checkpoint, got: {report_name}")

    overall_status = _require_str(payload, "overall_status")
    if overall_status not in {"ready", "blocked"}:
        raise ValueError("overall_status must be ready|blocked")

    smoke_gate_status = _require_str(payload, "smoke_gate_status")
    if smoke_gate_status not in {"ready", "blocked"}:
        raise ValueError("smoke_gate_status must be ready|blocked")
    wrapper_gate_status = _require_str(payload, "wrapper_gate_status")
    if wrapper_gate_status not in {"ready", "blocked"}:
        raise ValueError("wrapper_gate_status must be ready|blocked")
    function_status = _require_str(payload, "function_status")
    if function_status not in {"ready", "blocked"}:
        raise ValueError("function_status must be ready|blocked")

    _require_str(payload, "run_id")
    _require_str(payload, "workspace_root")
    _require_abs_existing_path(payload.get("smoke_gate_summary_json"), "smoke_gate_summary_json")
    _require_abs_existing_path(payload.get("wrapper_gate_summary_json"), "wrapper_gate_summary_json")
    _require_abs_existing_path(payload.get("function_summary_json"), "function_summary_json")
    _require_abs_existing_path(payload.get("progress_snapshot_json"), "progress_snapshot_json")
    _require_abs_existing_path(
        payload.get("migration_summary_json"),
        "migration_summary_json",
        optional=True,
    )
    _require_bool(payload, "progress_overall_ready")

    checks = payload.get("checkpoint_checks")
    if not isinstance(checks, Mapping):
        raise ValueError("checkpoint_checks must be object")
    check_map = dict(checks)
    for key in REQUIRED_CHECK_KEYS:
        if key not in check_map:
            raise ValueError(f"checkpoint_checks missing key: {key}")
        if not isinstance(check_map[key], bool):
            raise ValueError(f"checkpoint_checks.{key} must be bool")

    expected_status = "ready" if all(bool(check_map[k]) for k in REQUIRED_CHECK_KEYS) else "blocked"
    if overall_status != expected_status:
        raise ValueError(
            f"overall_status mismatch with checkpoint_checks: overall_status={overall_status}, expected={expected_status}"
        )

    if smoke_gate_status != ("ready" if bool(check_map["smoke_gate_pass"]) else "blocked"):
        raise ValueError("smoke_gate_status mismatch with checkpoint_checks.smoke_gate_pass")
    if wrapper_gate_status != ("ready" if bool(check_map["wrapper_gate_pass"]) else "blocked"):
        raise ValueError("wrapper_gate_status mismatch with checkpoint_checks.wrapper_gate_pass")
    if function_status != ("ready" if bool(check_map["function_api_stage_ready"]) else "blocked"):
        raise ValueError("function_status mismatch with checkpoint_checks.function_api_stage_ready")

    commands = payload.get("commands")
    if not isinstance(commands, Mapping):
        raise ValueError("commands must be object")
    _validate_command_block(commands, "smoke_gate")
    _validate_command_block(commands, "wrapper_gate")
    _validate_command_block(commands, "progress_snapshot")
    _validate_command_block(commands, "migration_stepwise", allow_skipped=True)
    _validate_command_block(commands, "function_progress")

    if args.require_ready and overall_status != "ready":
        raise ValueError("overall_status must be ready when --require-ready is set")

    print("validate_radarsimpy_readiness_checkpoint_report: pass")
    print(f"  summary_json: {summary_json}")
    print(f"  overall_status: {overall_status}")
    print(f"  smoke_gate_status: {smoke_gate_status}")
    print(f"  wrapper_gate_status: {wrapper_gate_status}")
    print(f"  function_status: {function_status}")


if __name__ == "__main__":
    main()
