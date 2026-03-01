#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping


ALLOWED_CAMPAIGN_STATUS = ("stable", "unstable")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate PO-SBR physical full-track stability campaign report")
    p.add_argument("--summary-json", required=True, help="Stability campaign summary JSON path")
    p.add_argument(
        "--require-stable",
        action="store_true",
        help="Fail validation unless campaign_status=stable",
    )
    return p.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("summary json must be object")
    return payload


def _assert_str_list(value: Any, key_name: str) -> List[str]:
    if not isinstance(value, list):
        raise ValueError(f"{key_name} must be list")
    out: List[str] = []
    for idx, item in enumerate(value):
        text = str(item).strip()
        if text == "":
            raise ValueError(f"{key_name}[{idx}] must be non-empty string")
        out.append(text)
    return out


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary_json).expanduser().resolve()
    if not summary_path.exists():
        raise FileNotFoundError(f"summary report not found: {summary_path}")

    payload = _load_json(summary_path)
    if int(payload.get("version", 0)) != 1:
        raise ValueError("version must be 1")

    campaign_status = str(payload.get("campaign_status", "")).strip()
    if campaign_status not in ALLOWED_CAMPAIGN_STATUS:
        raise ValueError(f"campaign_status invalid: {campaign_status}")

    requested_runs = int(payload.get("requested_runs", -1))
    if requested_runs <= 0:
        raise ValueError("requested_runs must be > 0")

    blockers = _assert_str_list(payload.get("blockers"), "blockers")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be list")
    if len(rows) != requested_runs:
        raise ValueError("rows length must match requested_runs")

    seen_indices = set()
    run_error_count = 0
    full_track_blocked_count = 0
    matrix_not_ready_count = 0
    gate_blocked_run_count = 0
    stable_run_count = 0

    for idx, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"rows[{idx}] must be object")
        run_index = int(row.get("run_index", 0))
        if run_index <= 0:
            raise ValueError(f"rows[{idx}].run_index must be > 0")
        if run_index in seen_indices:
            raise ValueError(f"rows[{idx}] duplicate run_index: {run_index}")
        seen_indices.add(run_index)

        run_root = str(row.get("run_root", "")).strip()
        matrix_summary_json = str(row.get("matrix_summary_json", "")).strip()
        bundle_summary_json = str(row.get("bundle_summary_json", "")).strip()
        for key_name, value in (
            ("run_root", run_root),
            ("matrix_summary_json", matrix_summary_json),
            ("bundle_summary_json", bundle_summary_json),
        ):
            if value == "":
                raise ValueError(f"rows[{idx}].{key_name} missing")
            p = Path(value).expanduser()
            if not p.is_absolute():
                raise ValueError(f"rows[{idx}].{key_name} must be absolute path")

        run_bundle = row.get("run_bundle")
        if not isinstance(run_bundle, Mapping):
            raise ValueError(f"rows[{idx}].run_bundle must be object")
        if "ok" not in run_bundle or "return_code" not in run_bundle or "cmd" not in run_bundle:
            raise ValueError(f"rows[{idx}].run_bundle missing required keys")

        run_ok = bool(row.get("run_ok", False))
        if not run_ok:
            run_error_count += 1
            continue

        full_track_status = str(row.get("full_track_status", "")).strip()
        matrix_status = str(row.get("matrix_status", "")).strip()
        gate_blocked_profile_count = int(row.get("gate_blocked_profile_count", 0) or 0)
        if full_track_status != "ready":
            full_track_blocked_count += 1
        if matrix_status != "ready":
            matrix_not_ready_count += 1
        if gate_blocked_profile_count > 0:
            gate_blocked_run_count += 1
        if full_track_status == "ready":
            stable_run_count += 1

    expected_blockers: List[str] = []
    if run_error_count > 0:
        expected_blockers.append("bundle_runner_failed")
    if full_track_blocked_count > 0:
        expected_blockers.append("full_track_bundle_not_ready")
    if matrix_not_ready_count > 0:
        expected_blockers.append("matrix_not_ready")
    if gate_blocked_run_count > 0:
        expected_blockers.append("gate_profiles_blocked")
    if sorted(expected_blockers) != sorted(blockers):
        raise ValueError(f"blockers mismatch: got={blockers}, expected={expected_blockers}")

    expected_status = "stable" if len(expected_blockers) == 0 else "unstable"
    if campaign_status != expected_status:
        raise ValueError(f"campaign_status mismatch: got={campaign_status}, expected={expected_status}")

    summary = payload.get("summary")
    if not isinstance(summary, Mapping):
        raise ValueError("summary must be object")
    if int(summary.get("requested_runs", -1)) != requested_runs:
        raise ValueError("summary.requested_runs mismatch")
    if int(summary.get("completed_runs", -1)) != len(rows):
        raise ValueError("summary.completed_runs mismatch")
    if int(summary.get("run_error_count", -1)) != run_error_count:
        raise ValueError("summary.run_error_count mismatch")
    if int(summary.get("full_track_blocked_count", -1)) != full_track_blocked_count:
        raise ValueError("summary.full_track_blocked_count mismatch")
    if int(summary.get("matrix_not_ready_count", -1)) != matrix_not_ready_count:
        raise ValueError("summary.matrix_not_ready_count mismatch")
    if int(summary.get("gate_blocked_run_count", -1)) != gate_blocked_run_count:
        raise ValueError("summary.gate_blocked_run_count mismatch")
    if int(summary.get("stable_run_count", -1)) != stable_run_count:
        raise ValueError("summary.stable_run_count mismatch")

    if args.require_stable and campaign_status != "stable":
        raise ValueError(f"campaign_status must be stable, got: {campaign_status}")

    print("validate_po_sbr_physical_full_track_stability_report: pass")
    print(f"  summary_json: {summary_path}")
    print(f"  campaign_status: {campaign_status}")
    print(f"  requested_runs: {requested_runs}")


if __name__ == "__main__":
    main()
