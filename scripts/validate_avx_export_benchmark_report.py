#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, Mapping


ALLOWED_STATUS = ("ready", "blocked")
ALLOWED_PHYSICS_CLAIMS = (
    "unsupported_without_truth",
    "candidate_better_vs_truth",
    "candidate_worse_vs_truth",
    "equivalent_vs_truth",
    "inconclusive",
)
ALLOWED_USABILITY_CLAIMS = ("candidate_better", "candidate_worse", "equivalent")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate AVX export benchmark report")
    p.add_argument("--summary-json", required=True, help="Benchmark summary JSON path")
    p.add_argument(
        "--require-ready",
        action="store_true",
        help="Fail validation if comparison_status != ready",
    )
    p.add_argument(
        "--require-truth-comparison",
        action="store_true",
        help="Fail validation if truth comparison fields are missing/unavailable",
    )
    p.add_argument(
        "--require-candidate-better-physics",
        action="store_true",
        help="Fail validation unless better_than_reference_physics_claim=candidate_better_vs_truth",
    )
    return p.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("summary json must be object")
    return payload


def _require_mapping(value: Any, key_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{key_name} must be object")
    return value


def _require_bool(value: Any, key_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{key_name} must be bool")
    return bool(value)


def _validate_parity_section(section: Mapping[str, Any], key_name: str) -> None:
    available = _require_bool(section.get("available"), f"{key_name}.available")
    if not available:
        reason = str(section.get("reason", "")).strip()
        if reason == "":
            raise ValueError(f"{key_name}.reason required when available=false")
        return

    parity = _require_mapping(section.get("parity"), f"{key_name}.parity")
    _require_bool(parity.get("pass"), f"{key_name}.parity.pass")
    metrics = parity.get("metrics")
    if not isinstance(metrics, Mapping):
        raise ValueError(f"{key_name}.parity.metrics must be object")
    failures = parity.get("failures")
    if not isinstance(failures, list):
        raise ValueError(f"{key_name}.parity.failures must be list")


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary_json).expanduser().resolve()
    if not summary_path.exists():
        raise FileNotFoundError(f"summary report not found: {summary_path}")

    payload = _load_json(summary_path)

    version = int(payload.get("version", 0))
    if version != 1:
        raise ValueError(f"version must be 1, got: {version}")

    candidate_label = str(payload.get("candidate_label", "")).strip()
    reference_label = str(payload.get("reference_label", "")).strip()
    if candidate_label == "":
        raise ValueError("candidate_label must be non-empty")
    if reference_label == "":
        raise ValueError("reference_label must be non-empty")

    status = str(payload.get("comparison_status", "")).strip()
    if status not in ALLOWED_STATUS:
        raise ValueError(f"comparison_status invalid: {status}")

    blockers = payload.get("blockers")
    if not isinstance(blockers, list):
        raise ValueError("blockers must be list")
    if status == "ready" and len(blockers) != 0:
        raise ValueError("ready report must have empty blockers")
    if status == "blocked" and len(blockers) == 0:
        raise ValueError("blocked report must have non-empty blockers")

    physics = _require_mapping(payload.get("physics"), "physics")
    cand_vs_ref = _require_mapping(physics.get("candidate_vs_reference"), "physics.candidate_vs_reference")
    _validate_parity_section(cand_vs_ref, "physics.candidate_vs_reference")

    claim = str(physics.get("better_than_reference_physics_claim", "")).strip()
    if claim not in ALLOWED_PHYSICS_CLAIMS:
        raise ValueError(f"invalid better_than_reference_physics_claim: {claim}")

    details = physics.get("better_than_reference_physics_details")
    if details is not None and (not isinstance(details, Mapping)):
        raise ValueError("physics.better_than_reference_physics_details must be object or null")

    candidate_vs_truth = physics.get("candidate_vs_truth")
    reference_vs_truth = physics.get("reference_vs_truth")
    if candidate_vs_truth is not None:
        _validate_parity_section(
            _require_mapping(candidate_vs_truth, "physics.candidate_vs_truth"),
            "physics.candidate_vs_truth",
        )
    if reference_vs_truth is not None:
        _validate_parity_section(
            _require_mapping(reference_vs_truth, "physics.reference_vs_truth"),
            "physics.reference_vs_truth",
        )

    path_section = _require_mapping(payload.get("path_comparison"), "path_comparison")
    if "candidate_path_summary" not in path_section:
        raise ValueError("path_comparison.candidate_path_summary missing")
    if "reference_path_summary" not in path_section:
        raise ValueError("path_comparison.reference_path_summary missing")
    _require_mapping(path_section.get("comparison"), "path_comparison.comparison")

    adc_section = _require_mapping(payload.get("adc_comparison"), "adc_comparison")
    if "comparison" not in adc_section:
        raise ValueError("adc_comparison.comparison missing")

    function_usability = _require_mapping(payload.get("function_usability"), "function_usability")
    cand_fn = _require_mapping(function_usability.get("candidate"), "function_usability.candidate")
    ref_fn = _require_mapping(function_usability.get("reference"), "function_usability.reference")
    cand_score = float(cand_fn.get("score", -1.0))
    ref_score = float(ref_fn.get("score", -1.0))
    if not (0.0 <= cand_score <= 1.0):
        raise ValueError("function_usability.candidate.score must be in [0,1]")
    if not (0.0 <= ref_score <= 1.0):
        raise ValueError("function_usability.reference.score must be in [0,1]")
    fn_claim = str(function_usability.get("better_than_reference_function_usability_claim", "")).strip()
    if fn_claim not in ALLOWED_USABILITY_CLAIMS:
        raise ValueError(f"invalid better_than_reference_function_usability_claim: {fn_claim}")

    summary = _require_mapping(payload.get("summary"), "summary")
    if bool(summary.get("candidate_vs_reference_parity_available", False)):
        if summary.get("candidate_vs_reference_parity_fail_count") is None:
            raise ValueError("summary.candidate_vs_reference_parity_fail_count required when parity available")

    if args.require_ready and status != "ready":
        raise ValueError(f"comparison_status must be ready, got: {status}")

    if args.require_truth_comparison:
        if candidate_vs_truth is None or reference_vs_truth is None:
            raise ValueError("truth comparison missing while --require-truth-comparison")
        if not bool(candidate_vs_truth.get("available", False)):
            raise ValueError("physics.candidate_vs_truth.available must be true")
        if not bool(reference_vs_truth.get("available", False)):
            raise ValueError("physics.reference_vs_truth.available must be true")
        if claim == "unsupported_without_truth":
            raise ValueError("better_than_reference_physics_claim cannot be unsupported_without_truth")

    if args.require_candidate_better_physics and claim != "candidate_better_vs_truth":
        raise ValueError(
            "better_than_reference_physics_claim must be candidate_better_vs_truth, "
            f"got: {claim}"
        )

    print("validate_avx_export_benchmark_report: pass")
    print(f"  summary_json: {summary_path}")
    print(f"  comparison_status: {status}")
    print(f"  better_than_reference_physics_claim: {claim}")
    print(f"  better_than_reference_function_usability_claim: {fn_claim}")


if __name__ == "__main__":
    main()
