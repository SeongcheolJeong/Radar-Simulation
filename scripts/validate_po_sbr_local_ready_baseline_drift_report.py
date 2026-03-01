#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate PO-SBR local-ready baseline drift report")
    p.add_argument("--report-json", required=True, help="Drift report JSON path")
    p.add_argument(
        "--require-match",
        action="store_true",
        help="Fail validation unless drift_verdict=match",
    )
    return p.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("report json must be object")
    return payload


def _assert_abs_existing_path(value: Any, key_name: str) -> None:
    text = str(value).strip()
    if text == "":
        raise ValueError(f"{key_name} missing")
    path = Path(text).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{key_name} must be absolute path")
    if not path.exists():
        raise ValueError(f"{key_name} not found: {path}")


def _assert_status_snapshot(value: Any, key_name: str) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{key_name} must be object")
    required = (
        "overall_status",
        "golden_path_status",
        "kpi_campaign_status",
        "kpi_scenario_matrix_status",
        "gate_lock_status",
    )
    for key in required:
        if key not in value:
            raise ValueError(f"{key_name}.{key} missing")


def _assert_differences(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError("differences must be list")
    out: List[Dict[str, Any]] = []
    for idx, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ValueError(f"differences[{idx}] must be object")
        field = str(item.get("field", "")).strip()
        if field == "":
            raise ValueError(f"differences[{idx}].field missing")
        out.append(dict(item))
    return out


def main() -> None:
    args = parse_args()
    report_path = Path(args.report_json).expanduser().resolve()
    if not report_path.exists():
        raise FileNotFoundError(f"report not found: {report_path}")

    payload = _load_json(report_path)
    if int(payload.get("version", 0)) != 1:
        raise ValueError("version must be 1")

    _assert_abs_existing_path(payload.get("baseline_manifest_json"), "baseline_manifest_json")
    _assert_abs_existing_path(payload.get("baseline_summary_json"), "baseline_summary_json")
    _assert_abs_existing_path(payload.get("candidate_summary_json"), "candidate_summary_json")

    drift_verdict = str(payload.get("drift_verdict", "")).strip()
    if drift_verdict not in ("match", "mismatch"):
        raise ValueError(f"drift_verdict invalid: {drift_verdict}")

    differences = _assert_differences(payload.get("differences"))
    difference_count = int(payload.get("difference_count", -1))
    if difference_count != len(differences):
        raise ValueError("difference_count mismatch")

    blockers = payload.get("blockers")
    if not isinstance(blockers, list):
        raise ValueError("blockers must be list")

    _assert_status_snapshot(payload.get("baseline_status_snapshot"), "baseline_status_snapshot")
    _assert_status_snapshot(payload.get("candidate_status_snapshot"), "candidate_status_snapshot")

    expected_verdict = "match" if len(differences) == 0 else "mismatch"
    if drift_verdict != expected_verdict:
        raise ValueError(
            f"drift_verdict mismatch: got={drift_verdict}, expected={expected_verdict}"
        )

    if args.require_match and drift_verdict != "match":
        raise ValueError(f"drift_verdict must be match, got: {drift_verdict}")

    print("validate_po_sbr_local_ready_baseline_drift_report: pass")
    print(f"  report_json: {report_path}")
    print(f"  drift_verdict: {drift_verdict}")
    print(f"  difference_count: {len(differences)}")


if __name__ == "__main__":
    main()
