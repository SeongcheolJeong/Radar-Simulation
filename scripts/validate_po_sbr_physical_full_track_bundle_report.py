#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping


ALLOWED_FULL_TRACK_STATUS = ("ready", "blocked")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate PO-SBR physical full-track bundle report")
    p.add_argument("--summary-json", required=True, help="Full-track bundle summary JSON path")
    p.add_argument(
        "--require-ready",
        action="store_true",
        help="Fail validation unless full_track_status=ready",
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

    full_track_status = str(payload.get("full_track_status", "")).strip()
    if full_track_status not in ALLOWED_FULL_TRACK_STATUS:
        raise ValueError(f"full_track_status invalid: {full_track_status}")

    required_profiles = _assert_str_list(payload.get("required_profiles"), "required_profiles")
    gate_profile_families = _assert_str_list(payload.get("gate_profile_families"), "gate_profile_families")
    if len(gate_profile_families) == 0:
        raise ValueError("gate_profile_families must be non-empty")
    missing_required_profiles = _assert_str_list(
        payload.get("missing_required_profiles"),
        "missing_required_profiles",
    )
    blockers = _assert_str_list(payload.get("blockers"), "blockers")

    matrix_status = str(payload.get("matrix_status", "")).strip()
    if matrix_status not in ("ready", "blocked", "failed", ""):
        raise ValueError(f"matrix_status invalid: {matrix_status}")

    source_matrix_summary_json = str(payload.get("source_matrix_summary_json", "")).strip()
    if source_matrix_summary_json == "":
        raise ValueError("source_matrix_summary_json missing")
    matrix_summary_path = Path(source_matrix_summary_json).expanduser()
    if not matrix_summary_path.is_absolute():
        raise ValueError("source_matrix_summary_json must be absolute path")
    if not matrix_summary_path.exists():
        raise ValueError(f"source_matrix_summary_json not found: {matrix_summary_path}")

    matrix_run = payload.get("matrix_run")
    if not isinstance(matrix_run, Mapping):
        raise ValueError("matrix_run must be object")
    if "ok" not in matrix_run or "return_code" not in matrix_run or "cmd" not in matrix_run:
        raise ValueError("matrix_run missing required keys")

    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be list")

    seen_profiles = set()
    po_sbr_executed_count = 0
    for idx, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"rows[{idx}] must be object")
        profile = str(row.get("profile", "")).strip()
        if profile == "":
            raise ValueError(f"rows[{idx}].profile missing")
        if profile in seen_profiles:
            raise ValueError(f"rows duplicate profile: {profile}")
        seen_profiles.add(profile)
        if str(row.get("po_sbr_status", "")).strip() == "executed":
            po_sbr_executed_count += 1
        if row.get("po_sbr_path_count") is not None:
            if int(row.get("po_sbr_path_count", -1)) < 0:
                raise ValueError(f"rows[{idx}].po_sbr_path_count must be >= 0")

    required_set = set(required_profiles)
    missing_set = set(missing_required_profiles)
    if not missing_set.issubset(required_set):
        raise ValueError("missing_required_profiles must be subset of required_profiles")

    expected_missing = sorted(list(required_set - seen_profiles))
    if sorted(missing_required_profiles) != expected_missing:
        raise ValueError("missing_required_profiles mismatch")

    summary = payload.get("summary")
    if not isinstance(summary, Mapping):
        raise ValueError("summary must be object")
    if int(summary.get("required_profile_count", -1)) != len(required_profiles):
        raise ValueError("summary.required_profile_count mismatch")
    if int(summary.get("present_profile_count", -1)) != len(required_profiles) - len(missing_required_profiles):
        raise ValueError("summary.present_profile_count mismatch")
    if int(summary.get("missing_profile_count", -1)) != len(missing_required_profiles):
        raise ValueError("summary.missing_profile_count mismatch")
    if int(summary.get("po_sbr_executed_profile_count", -1)) != po_sbr_executed_count:
        raise ValueError("summary.po_sbr_executed_profile_count mismatch")

    expected_status = "ready" if (len(missing_required_profiles) == 0 and len(blockers) == 0) else "blocked"
    if full_track_status != expected_status:
        raise ValueError(f"full_track_status mismatch: got={full_track_status}, expected={expected_status}")

    if args.require_ready and full_track_status != "ready":
        raise ValueError(f"full_track_status must be ready, got: {full_track_status}")

    print("validate_po_sbr_physical_full_track_bundle_report: pass")
    print(f"  summary_json: {summary_path}")
    print(f"  full_track_status: {full_track_status}")
    print(f"  required_profile_count: {len(required_profiles)}")


if __name__ == "__main__":
    main()
