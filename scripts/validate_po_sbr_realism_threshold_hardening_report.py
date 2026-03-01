#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping


ALLOWED_HARDENING_STATUS = ("hardened", "blocked")
ALLOWED_PROFILE_STATUS = ("ready", "blocked", "failed")
DEFAULT_REALISM_GATE_CANDIDATE = "realism_tight_v2"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate PO-SBR realism threshold hardening report")
    p.add_argument("--summary-json", required=True, help="Hardening summary JSON path")
    p.add_argument(
        "--require-hardened",
        action="store_true",
        help="Fail validation unless hardening_status=hardened",
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

    hardening_status = str(payload.get("hardening_status", "")).strip()
    if hardening_status not in ALLOWED_HARDENING_STATUS:
        raise ValueError(f"hardening_status invalid: {hardening_status}")

    blockers = _assert_str_list(payload.get("blockers"), "blockers")
    threshold_profiles = _assert_str_list(payload.get("threshold_profiles"), "threshold_profiles")
    realism_profile_names = _assert_str_list(payload.get("realism_profile_names"), "realism_profile_names")
    realism_gate_candidate = str(
        payload.get("realism_gate_candidate", DEFAULT_REALISM_GATE_CANDIDATE)
    ).strip()
    if realism_gate_candidate == "":
        raise ValueError("realism_gate_candidate must be non-empty")

    source_full_track_bundle_summary_json = str(
        payload.get("source_full_track_bundle_summary_json", "")
    ).strip()
    if source_full_track_bundle_summary_json == "":
        raise ValueError("source_full_track_bundle_summary_json missing")
    source_bundle_path = Path(source_full_track_bundle_summary_json).expanduser()
    if not source_bundle_path.is_absolute():
        raise ValueError("source_full_track_bundle_summary_json must be absolute path")
    if not source_bundle_path.exists():
        raise ValueError(f"source_full_track_bundle_summary_json not found: {source_bundle_path}")

    profile_rows = payload.get("profiles")
    if not isinstance(profile_rows, list):
        raise ValueError("profiles must be list")
    if len(profile_rows) != len(threshold_profiles):
        raise ValueError("profiles length must match threshold_profiles")

    seen_threshold_profiles = set()
    status_by_threshold: Dict[str, str] = {}
    threshold_ready_count = 0
    threshold_failed_count = 0
    for idx, row in enumerate(profile_rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"profiles[{idx}] must be object")
        threshold_profile = str(row.get("threshold_profile", "")).strip()
        if threshold_profile == "":
            raise ValueError(f"profiles[{idx}].threshold_profile missing")
        if threshold_profile in seen_threshold_profiles:
            raise ValueError(f"duplicate threshold_profile row: {threshold_profile}")
        seen_threshold_profiles.add(threshold_profile)
        status = str(row.get("status", "")).strip()
        if status not in ALLOWED_PROFILE_STATUS:
            raise ValueError(f"profiles[{idx}].status invalid: {status}")
        status_by_threshold[threshold_profile] = status
        if status == "ready":
            threshold_ready_count += 1
        else:
            threshold_failed_count += 1

        summary = row.get("summary")
        if not isinstance(summary, Mapping):
            raise ValueError(f"profiles[{idx}].summary must be object")
        profile_count = int(summary.get("profile_count", -1))
        ready_profile_count = int(summary.get("ready_profile_count", -1))
        blocked_profile_count = int(summary.get("blocked_profile_count", -1))
        failed_profile_count = int(summary.get("failed_profile_count", -1))
        if profile_count != len(realism_profile_names):
            raise ValueError(f"profiles[{idx}].summary.profile_count mismatch")
        if ready_profile_count + blocked_profile_count + failed_profile_count != profile_count:
            raise ValueError(f"profiles[{idx}].summary counts inconsistent")

        rows = row.get("rows")
        if not isinstance(rows, list):
            raise ValueError(f"profiles[{idx}].rows must be list")
        if len(rows) != len(realism_profile_names):
            raise ValueError(f"profiles[{idx}].rows length mismatch")

        seen_profiles = set()
        for j, prow in enumerate(rows):
            if not isinstance(prow, Mapping):
                raise ValueError(f"profiles[{idx}].rows[{j}] must be object")
            pname = str(prow.get("profile", "")).strip()
            if pname == "":
                raise ValueError(f"profiles[{idx}].rows[{j}].profile missing")
            if pname in seen_profiles:
                raise ValueError(f"profiles[{idx}] duplicate realism profile row: {pname}")
            seen_profiles.add(pname)
            run_ok = bool(prow.get("run_ok", False))
            campaign_status = str(prow.get("campaign_status", "")).strip()
            if run_ok and campaign_status not in ("ready", "blocked"):
                raise ValueError(
                    f"profiles[{idx}].rows[{j}] campaign_status invalid for run_ok row: {campaign_status}"
                )

            for key in ("thresholds_json", "output_kpi_json", "source_golden_summary_json"):
                v = str(prow.get(key, "")).strip()
                if v == "":
                    raise ValueError(f"profiles[{idx}].rows[{j}].{key} missing")
                p = Path(v).expanduser()
                if not p.is_absolute():
                    raise ValueError(f"profiles[{idx}].rows[{j}].{key} must be absolute path")

        if sorted(seen_profiles) != sorted(realism_profile_names):
            raise ValueError(f"profiles[{idx}] realism profile set mismatch")

    if sorted(seen_threshold_profiles) != sorted(threshold_profiles):
        raise ValueError("threshold_profiles mismatch")
    if realism_gate_candidate not in seen_threshold_profiles:
        raise ValueError("realism_gate_candidate must be included in threshold_profiles")
    derived_candidate_status = str(status_by_threshold.get(realism_gate_candidate, "")).strip()
    if derived_candidate_status == "":
        raise ValueError("failed to derive realism_gate_candidate status")
    candidate_status_from_payload = payload.get("realism_gate_candidate_status")
    if candidate_status_from_payload is not None:
        candidate_status = str(candidate_status_from_payload).strip()
        if candidate_status != derived_candidate_status:
            raise ValueError(
                "realism_gate_candidate_status mismatch: "
                f"got={candidate_status}, expected={derived_candidate_status}"
            )
    else:
        candidate_status = derived_candidate_status

    summary = payload.get("summary")
    if not isinstance(summary, Mapping):
        raise ValueError("summary must be object")
    if int(summary.get("threshold_profile_count", -1)) != len(threshold_profiles):
        raise ValueError("summary.threshold_profile_count mismatch")
    if int(summary.get("threshold_ready_count", -1)) != threshold_ready_count:
        raise ValueError("summary.threshold_ready_count mismatch")
    if int(summary.get("threshold_failed_count", -1)) != threshold_failed_count:
        raise ValueError("summary.threshold_failed_count mismatch")
    if int(summary.get("realism_profile_count", -1)) != len(realism_profile_names):
        raise ValueError("summary.realism_profile_count mismatch")
    if "realism_gate_candidate_status" in summary:
        if str(summary.get("realism_gate_candidate_status", "")).strip() != derived_candidate_status:
            raise ValueError("summary.realism_gate_candidate_status mismatch")

    expected_status = (
        "hardened"
        if threshold_failed_count == 0 and len(blockers) == 0 and derived_candidate_status == "ready"
        else "blocked"
    )
    if hardening_status != expected_status:
        raise ValueError(f"hardening_status mismatch: got={hardening_status}, expected={expected_status}")

    if args.require_hardened and hardening_status != "hardened":
        raise ValueError(f"hardening_status must be hardened, got: {hardening_status}")

    print("validate_po_sbr_realism_threshold_hardening_report: pass")
    print(f"  summary_json: {summary_path}")
    print(f"  hardening_status: {hardening_status}")
    print(f"  threshold_profile_count: {len(threshold_profiles)}")


if __name__ == "__main__":
    main()
