#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping


REQUIRED_SOURCE_NAMES = ("openEMS", "CSXCAD", "gprMax")


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


def _validate_policy(policy: Mapping[str, Any]) -> None:
    if int(policy.get("version", 0)) != 1:
        raise ValueError("policy.version must be 1")
    if _as_nonempty_str(policy.get("policy_id"), "policy.policy_id") != "em_solver_packaging_license_boundary_v1":
        raise ValueError("policy.policy_id mismatch")
    _as_nonempty_str(policy.get("generated_at_utc"), "policy.generated_at_utc")
    _as_nonempty_str(policy.get("scope"), "policy.scope")

    sources = policy.get("sources")
    if not isinstance(sources, list) or len(sources) < 3:
        raise ValueError("policy.sources must be list with >=3 entries")
    by_name = {}
    for i, row in enumerate(sources):
        entry = _as_obj(row, f"policy.sources[{i}]")
        name = _as_nonempty_str(entry.get("name"), f"policy.sources[{i}].name")
        _as_nonempty_str(entry.get("repository"), f"policy.sources[{i}].repository")
        _as_nonempty_str(entry.get("license"), f"policy.sources[{i}].license")
        by_name[name] = entry
    for name in REQUIRED_SOURCE_NAMES:
        if name not in by_name:
            raise ValueError(f"policy.sources missing required solver entry: {name}")

    dist = _as_obj(policy.get("distribution_policy"), "policy.distribution_policy")
    if _as_bool(
        dist.get("product_binary_may_bundle_em_solver"),
        "policy.distribution_policy.product_binary_may_bundle_em_solver",
    ):
        raise ValueError("product binary bundling must remain disabled for EM solvers")
    _as_bool(
        dist.get("service_boundary_required"),
        "policy.distribution_policy.service_boundary_required",
    )
    _as_bool(
        dist.get("shipping_manifold_assets_only_allowed"),
        "policy.distribution_policy.shipping_manifold_assets_only_allowed",
    )
    if _as_bool(
        dist.get("runtime_solver_dependency_in_core_pipeline"),
        "policy.distribution_policy.runtime_solver_dependency_in_core_pipeline",
    ):
        raise ValueError("core pipeline must not require EM solver runtime")

    modes = dist.get("solver_invocation_mode")
    if not isinstance(modes, list) or len(modes) <= 0:
        raise ValueError("policy.distribution_policy.solver_invocation_mode must be non-empty list")
    mode_set = {str(x).strip() for x in modes}
    if "external_process" not in mode_set:
        raise ValueError("solver_invocation_mode must include external_process")

    controls = _as_obj(policy.get("compliance_controls"), "policy.compliance_controls")
    for key in (
        "must_track_solver_commits_in_reference_locks",
        "must_record_solver_license_snapshot",
        "must_run_legal_review_before_distributable_packaging",
        "must_keep_solver_optional_in_runtime",
    ):
        if not _as_bool(controls.get(key), f"policy.compliance_controls.{key}"):
            raise ValueError(f"policy.compliance_controls.{key} must be true")

    risk = _as_obj(policy.get("risk_classification"), "policy.risk_classification")
    for key in ("openems", "gprmax", "csxcad"):
        _as_nonempty_str(risk.get(key), f"policy.risk_classification.{key}")

    notes = policy.get("operator_notes")
    if not isinstance(notes, list) or len(notes) <= 0:
        raise ValueError("policy.operator_notes must be non-empty list")
    for i, line in enumerate(notes):
        _as_nonempty_str(line, f"policy.operator_notes[{i}]")


def _validate_reference_locks(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for name in REQUIRED_SOURCE_NAMES:
        pattern = rf"- {re.escape(name)}: ([0-9a-f]{{40}})"
        if re.search(pattern, text) is None:
            raise ValueError(f"reference-locks missing 40-hex commit for: {name}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate EM solver packaging/license policy contract")
    p.add_argument(
        "--policy-json",
        default="docs/em_solver_packaging_policy.json",
        help="Path to EM solver packaging policy JSON",
    )
    p.add_argument(
        "--reference-locks-md",
        default="external/reference-locks.md",
        help="Path to reference lock markdown",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    policy_json = Path(args.policy_json).expanduser().resolve()
    ref_md = Path(args.reference_locks_md).expanduser().resolve()

    policy = json.loads(policy_json.read_text(encoding="utf-8"))
    if not isinstance(policy, Mapping):
        raise ValueError("policy json must contain an object")

    _validate_policy(policy)
    _validate_reference_locks(ref_md)
    print("validate_em_solver_packaging_policy: pass")


if __name__ == "__main__":
    main()
