#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


def _as_obj(value: Any, key_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{key_name} must be object")
    return value


def _as_bool(value: Any, key_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{key_name} must be bool")
    return bool(value)


def _as_nonempty_str(value: Any, key_name: str) -> str:
    text = str(value).strip()
    if text == "":
        raise ValueError(f"{key_name} must be non-empty string")
    return text


def _as_int(value: Any, key_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{key_name} must be integer")
    if isinstance(value, int):
        return int(value)
    raise ValueError(f"{key_name} must be integer")


def _validate_policy(policy: Mapping[str, Any]) -> None:
    if int(policy.get("version", 0)) != 1:
        raise ValueError("policy.version must be 1")
    if _as_nonempty_str(policy.get("policy_id"), "policy.policy_id") != "radarsimpy_runtime_license_boundary_v1":
        raise ValueError("policy.policy_id mismatch")

    _as_nonempty_str(policy.get("generated_at_utc"), "policy.generated_at_utc")
    _as_nonempty_str(policy.get("scope"), "policy.scope")

    markers = policy.get("runtime_warning_markers")
    if not isinstance(markers, list) or len(markers) < 2:
        raise ValueError("policy.runtime_warning_markers must contain at least two entries")
    marker_set = set()
    for i, marker in enumerate(markers):
        marker_set.add(_as_nonempty_str(marker, f"policy.runtime_warning_markers[{i}]").lower())
    for required in ("no license file path provided", "running in free tier mode"):
        if required not in marker_set:
            raise ValueError(f"policy.runtime_warning_markers missing required marker: {required}")

    tiers = _as_obj(policy.get("tier_profiles"), "policy.tier_profiles")
    trial = _as_obj(tiers.get("trial"), "policy.tier_profiles.trial")
    production = _as_obj(tiers.get("production"), "policy.tier_profiles.production")

    if _as_int(trial.get("max_tx_channels"), "policy.tier_profiles.trial.max_tx_channels") != 1:
        raise ValueError("trial.max_tx_channels must be 1")
    if _as_int(trial.get("max_rx_channels"), "policy.tier_profiles.trial.max_rx_channels") != 1:
        raise ValueError("trial.max_rx_channels must be 1")
    if not _as_bool(
        trial.get("requires_trial_free_tier_geometry"),
        "policy.tier_profiles.trial.requires_trial_free_tier_geometry",
    ):
        raise ValueError("trial.requires_trial_free_tier_geometry must be true")
    if _as_bool(trial.get("allows_production_release"), "policy.tier_profiles.trial.allows_production_release"):
        raise ValueError("trial.allows_production_release must be false")

    if _as_int(production.get("min_tx_channels"), "policy.tier_profiles.production.min_tx_channels") < 2:
        raise ValueError("production.min_tx_channels must be >= 2")
    if _as_int(production.get("min_rx_channels"), "policy.tier_profiles.production.min_rx_channels") < 2:
        raise ValueError("production.min_rx_channels must be >= 2")
    if _as_bool(
        production.get("requires_trial_free_tier_geometry"),
        "policy.tier_profiles.production.requires_trial_free_tier_geometry",
    ):
        raise ValueError("production.requires_trial_free_tier_geometry must be false")
    if not _as_bool(
        production.get("allows_production_release"),
        "policy.tier_profiles.production.allows_production_release",
    ):
        raise ValueError("production.allows_production_release must be true")
    if not _as_bool(
        production.get("must_not_emit_free_tier_warning_markers"),
        "policy.tier_profiles.production.must_not_emit_free_tier_warning_markers",
    ):
        raise ValueError("production.must_not_emit_free_tier_warning_markers must be true")

    controls = _as_obj(policy.get("compliance_controls"), "policy.compliance_controls")
    for key in (
        "must_track_license_artifact_source",
        "must_record_runtime_tier_in_gate_reports",
        "must_fail_production_gate_on_free_tier_markers",
        "must_run_multichannel_pilot_for_production_release",
    ):
        if not _as_bool(controls.get(key), f"policy.compliance_controls.{key}"):
            raise ValueError(f"policy.compliance_controls.{key} must be true")

    notes = policy.get("operator_notes")
    if not isinstance(notes, list) or len(notes) <= 0:
        raise ValueError("policy.operator_notes must be non-empty list")
    for i, note in enumerate(notes):
        _as_nonempty_str(note, f"policy.operator_notes[{i}]")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate RadarSimPy runtime license policy contract")
    p.add_argument(
        "--policy-json",
        default="docs/radarsimpy_runtime_license_policy.json",
        help="Path to RadarSimPy runtime license policy JSON",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    policy_json = Path(args.policy_json).expanduser().resolve()

    policy = json.loads(policy_json.read_text(encoding="utf-8"))
    if not isinstance(policy, Mapping):
        raise ValueError("policy json must contain an object")

    _validate_policy(policy)
    print("validate_radarsimpy_runtime_license_policy: pass")


if __name__ == "__main__":
    main()
