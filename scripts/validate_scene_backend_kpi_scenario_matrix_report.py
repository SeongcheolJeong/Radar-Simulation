#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping


ALLOWED_MATRIX_STATUS = ("ready", "blocked", "failed")
PROFILE_FAMILY_BY_ID = {
    "single_target_range25_v1": "equivalence_strict",
    "single_target_az20_range25_v1": "equivalence_strict",
    "single_target_vel3_range25_v1": "equivalence_strict",
    "dual_target_split_range25_v1": "realism_informational",
    "single_target_material_loss_range25_v1": "realism_informational",
    "mesh_dihedral_range25_v1": "realism_informational",
    "mesh_trihedral_range25_v1": "realism_informational",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate scene backend KPI scenario matrix report")
    p.add_argument("--summary-json", required=True, help="Scenario matrix summary JSON path")
    p.add_argument(
        "--require-ready",
        action="store_true",
        help="Fail validation unless matrix_status=ready",
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

    profiles = _assert_str_list(payload.get("profiles"), "profiles")
    gate_profile_families_raw = payload.get("gate_profile_families")
    if gate_profile_families_raw is None:
        gate_profile_families = ["equivalence_strict"]
    else:
        gate_profile_families = _assert_str_list(
            gate_profile_families_raw,
            "gate_profile_families",
        )
    matrix_status = str(payload.get("matrix_status", "")).strip()
    if matrix_status not in ALLOWED_MATRIX_STATUS:
        raise ValueError(f"matrix_status invalid: {matrix_status}")

    summary = payload.get("summary")
    if not isinstance(summary, Mapping):
        raise ValueError("summary must be object")

    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be list")
    if len(rows) != len(profiles):
        raise ValueError("rows length must match profiles length")

    ready_count = 0
    blocked_count = 0
    run_error_count = 0
    gate_ready_count = 0
    gate_blocked_count = 0
    info_ready_count = 0
    info_blocked_count = 0
    gate_family_set = set(gate_profile_families)
    row_gate_flags: Dict[str, bool] = {}

    seen_profiles = set()
    for idx, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"rows[{idx}] must be object")
        profile = str(row.get("profile", "")).strip()
        if profile == "":
            raise ValueError(f"rows[{idx}].profile missing")
        if profile in seen_profiles:
            raise ValueError(f"duplicate profile row: {profile}")
        seen_profiles.add(profile)

        run_ok = bool(row.get("run_ok", False))
        campaign_status = str(row.get("campaign_status", "")).strip()
        profile_family = str(row.get("profile_family", "")).strip()
        if profile_family == "":
            profile_family = str(PROFILE_FAMILY_BY_ID.get(profile, "equivalence_strict"))
        gate_required_raw = row.get("gate_required")
        if gate_required_raw is None:
            gate_required = bool(profile_family in gate_family_set)
        else:
            gate_required = bool(gate_required_raw)
        expected_gate_required = bool(profile_family in gate_family_set)
        if gate_required != expected_gate_required:
            raise ValueError(
                f"rows[{idx}].gate_required mismatch for family={profile_family}: "
                f"got={gate_required}, expected={expected_gate_required}"
            )
        row_gate_flags[profile] = gate_required
        if run_ok:
            if campaign_status == "ready":
                ready_count += 1
                if gate_required:
                    gate_ready_count += 1
                else:
                    info_ready_count += 1
            elif campaign_status == "blocked":
                blocked_count += 1
                if gate_required:
                    gate_blocked_count += 1
                else:
                    info_blocked_count += 1
            else:
                raise ValueError(f"rows[{idx}] invalid campaign_status for run_ok row: {campaign_status}")
        else:
            run_error_count += 1

        for key in ("golden_summary_json", "kpi_summary_json"):
            path_text = str(row.get(key, "")).strip()
            if path_text == "":
                raise ValueError(f"rows[{idx}].{key} missing")
            p = Path(path_text).expanduser()
            if not p.is_absolute():
                raise ValueError(f"rows[{idx}].{key} must be absolute path")

        run_steps = row.get("run_steps")
        if not isinstance(run_steps, Mapping):
            raise ValueError(f"rows[{idx}].run_steps must be object")
        for key in ("run_golden", "validate_golden", "run_kpi", "validate_kpi"):
            if key not in run_steps:
                raise ValueError(f"rows[{idx}].run_steps missing key: {key}")

    if set(profiles) != seen_profiles:
        raise ValueError("rows profiles mismatch")

    if int(summary.get("profile_count", -1)) != len(profiles):
        raise ValueError("summary.profile_count mismatch")
    if int(summary.get("ready_profile_count", -1)) != ready_count:
        raise ValueError("summary.ready_profile_count mismatch")
    if int(summary.get("blocked_profile_count", -1)) != blocked_count:
        raise ValueError("summary.blocked_profile_count mismatch")
    if int(summary.get("failed_profile_count", -1)) != run_error_count:
        raise ValueError("summary.failed_profile_count mismatch")
    gate_profile_count = int(sum(1 for profile_name in profiles if bool(row_gate_flags.get(profile_name, False))))
    info_profile_count = int(len(profiles) - gate_profile_count)
    if "gate_profile_count" in summary:
        if int(summary.get("gate_profile_count", -1)) != gate_profile_count:
            raise ValueError("summary.gate_profile_count mismatch")
    if "gate_ready_profile_count" in summary:
        if int(summary.get("gate_ready_profile_count", -1)) != gate_ready_count:
            raise ValueError("summary.gate_ready_profile_count mismatch")
    if "gate_blocked_profile_count" in summary:
        if int(summary.get("gate_blocked_profile_count", -1)) != gate_blocked_count:
            raise ValueError("summary.gate_blocked_profile_count mismatch")
    if "informational_profile_count" in summary:
        if int(summary.get("informational_profile_count", -1)) != info_profile_count:
            raise ValueError("summary.informational_profile_count mismatch")
    if "informational_ready_profile_count" in summary:
        if int(summary.get("informational_ready_profile_count", -1)) != info_ready_count:
            raise ValueError("summary.informational_ready_profile_count mismatch")
    if "informational_blocked_profile_count" in summary:
        if int(summary.get("informational_blocked_profile_count", -1)) != info_blocked_count:
            raise ValueError("summary.informational_blocked_profile_count mismatch")

    expected_status = "ready"
    if run_error_count > 0:
        expected_status = "failed"
    elif gate_blocked_count > 0:
        expected_status = "blocked"
    if matrix_status != expected_status:
        raise ValueError(
            f"matrix_status mismatch: got={matrix_status}, expected={expected_status}"
        )

    if args.require_ready and matrix_status != "ready":
        raise ValueError(f"matrix_status must be ready, got: {matrix_status}")

    print("validate_scene_backend_kpi_scenario_matrix_report: pass")
    print(f"  summary_json: {summary_path}")
    print(f"  matrix_status: {matrix_status}")
    print(f"  profile_count: {len(profiles)}")


if __name__ == "__main__":
    main()
