#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping


ALLOWED_GATE_LOCK_STATUS = ("ready", "blocked")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate PO-SBR physical full-track gate-lock report")
    p.add_argument("--summary-json", required=True, help="Gate-lock summary JSON path")
    p.add_argument(
        "--require-ready",
        action="store_true",
        help="Fail validation unless gate_lock_status=ready",
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


def _assert_run_result(value: Any, key_name: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{key_name} must be object")
    if "ok" not in value:
        raise ValueError(f"{key_name}.ok missing")
    if "return_code" not in value:
        raise ValueError(f"{key_name}.return_code missing")
    if "cmd" not in value:
        raise ValueError(f"{key_name}.cmd missing")
    if not isinstance(value.get("cmd"), list) or len(value.get("cmd")) == 0:
        raise ValueError(f"{key_name}.cmd must be non-empty list")
    return dict(value)


def _assert_abs_path(value: Any, key_name: str) -> Path:
    text = str(value).strip()
    if text == "":
        raise ValueError(f"{key_name} missing")
    path = Path(text).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{key_name} must be absolute path")
    return path


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary_json).expanduser().resolve()
    if not summary_path.exists():
        raise FileNotFoundError(f"summary report not found: {summary_path}")

    payload = _load_json(summary_path)
    if int(payload.get("version", 0)) != 1:
        raise ValueError("version must be 1")

    gate_lock_status = str(payload.get("gate_lock_status", "")).strip()
    if gate_lock_status not in ALLOWED_GATE_LOCK_STATUS:
        raise ValueError(f"gate_lock_status invalid: {gate_lock_status}")

    blockers = _assert_str_list(payload.get("blockers"), "blockers")
    threshold_profiles = _assert_str_list(payload.get("threshold_profiles"), "threshold_profiles")
    realism_gate_candidate = str(payload.get("realism_gate_candidate", "")).strip()
    if realism_gate_candidate == "":
        raise ValueError("realism_gate_candidate missing")
    if realism_gate_candidate not in threshold_profiles:
        raise ValueError("realism_gate_candidate must be included in threshold_profiles")

    full_track_bundle_summary_json = _assert_abs_path(
        payload.get("full_track_bundle_summary_json"),
        "full_track_bundle_summary_json",
    )
    if not full_track_bundle_summary_json.exists():
        raise ValueError(f"full_track_bundle_summary_json not found: {full_track_bundle_summary_json}")

    stability = payload.get("stability")
    if not isinstance(stability, Mapping):
        raise ValueError("stability must be object")
    stability_run = _assert_run_result(stability.get("run"), "stability.run")
    stability_summary_json = _assert_abs_path(stability.get("summary_json"), "stability.summary_json")
    stability_status = str(stability.get("campaign_status", "")).strip()

    hardening = payload.get("hardening")
    if not isinstance(hardening, Mapping):
        raise ValueError("hardening must be object")
    hardening_run = _assert_run_result(hardening.get("run"), "hardening.run")
    hardening_summary_json = _assert_abs_path(hardening.get("summary_json"), "hardening.summary_json")
    hardening_status = str(hardening.get("hardening_status", "")).strip()
    hardening_candidate = str(hardening.get("realism_gate_candidate", "")).strip()
    hardening_candidate_status = str(hardening.get("realism_gate_candidate_status", "")).strip()

    summary = payload.get("summary")
    if not isinstance(summary, Mapping):
        raise ValueError("summary must be object")
    if int(summary.get("stability_runs_requested", -1)) <= 0:
        raise ValueError("summary.stability_runs_requested must be > 0")
    if int(summary.get("threshold_profile_count", -1)) != len(threshold_profiles):
        raise ValueError("summary.threshold_profile_count mismatch")
    if str(summary.get("stability_status", "")).strip() != stability_status:
        raise ValueError("summary.stability_status mismatch")
    if str(summary.get("hardening_status", "")).strip() != hardening_status:
        raise ValueError("summary.hardening_status mismatch")
    if str(summary.get("realism_gate_candidate_status", "")).strip() != hardening_candidate_status:
        raise ValueError("summary.realism_gate_candidate_status mismatch")

    expected_status = (
        "ready"
        if bool(stability_run.get("ok", False))
        and bool(hardening_run.get("ok", False))
        and stability_status == "stable"
        and hardening_status == "hardened"
        and hardening_candidate == realism_gate_candidate
        and hardening_candidate_status == "ready"
        and len(blockers) == 0
        else "blocked"
    )
    if gate_lock_status != expected_status:
        raise ValueError(f"gate_lock_status mismatch: got={gate_lock_status}, expected={expected_status}")

    if args.require_ready and gate_lock_status != "ready":
        raise ValueError(f"gate_lock_status must be ready, got: {gate_lock_status}")

    print("validate_po_sbr_physical_full_track_gate_lock_report: pass")
    print(f"  summary_json: {summary_path}")
    print(f"  gate_lock_status: {gate_lock_status}")
    print(f"  threshold_profile_count: {len(threshold_profiles)}")


if __name__ == "__main__":
    main()
