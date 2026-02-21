#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Analyze fit-aware measured replay batch summary and detect saturation-style "
            "pass-rate jumps that may indicate overly strong proxy weighting."
        )
    )
    p.add_argument("--batch-summary-json", required=True)
    p.add_argument("--output-json", required=True)
    p.add_argument("--min-baseline-candidate-count", type=int, default=64)
    p.add_argument("--high-pass-rate-threshold", type=float, default=0.98)
    p.add_argument("--large-pass-rate-delta-threshold", type=float, default=0.5)
    p.add_argument("--pass-status-change-ratio-threshold", type=float, default=0.8)
    p.add_argument(
        "--max-allowed-saturated-cases",
        type=int,
        default=0,
        help="If saturated case count exceeds this value, gate fails.",
    )
    return p.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json must be object: {path}")
    return payload


def _as_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return float(default)


def _as_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except (TypeError, ValueError):
        return int(default)


def _detect_case_saturation(
    case_row: Mapping[str, Any],
    min_baseline_candidate_count: int,
    high_pass_rate_threshold: float,
    large_pass_rate_delta_threshold: float,
    pass_status_change_ratio_threshold: float,
) -> Dict[str, Any]:
    baseline = case_row.get("baseline_summary", {})
    best = case_row.get("best_attempt", {})
    delta = best.get("delta", {}) if isinstance(best, Mapping) else {}
    replay = best.get("replay_summary", {}) if isinstance(best, Mapping) else {}

    candidate_count = _as_int(baseline.get("candidate_count", 0))
    baseline_pass_rate = _as_float(baseline.get("pass_rate", 0.0))
    fit_pass_rate = _as_float(replay.get("pass_rate", 0.0))
    pass_rate_delta = _as_float(delta.get("pass_rate_delta", 0.0))
    changed_count = _as_int(best.get("candidate_pass_status_changed", 0))
    change_ratio = (float(changed_count) / float(candidate_count)) if candidate_count > 0 else 0.0

    criteria = {
        "enough_candidates": bool(candidate_count >= int(min_baseline_candidate_count)),
        "high_fit_pass_rate": bool(fit_pass_rate >= float(high_pass_rate_threshold)),
        "large_pass_rate_delta": bool(pass_rate_delta >= float(large_pass_rate_delta_threshold)),
        "large_pass_status_change_ratio": bool(
            change_ratio >= float(pass_status_change_ratio_threshold)
        ),
    }
    saturated = all(criteria.values())

    reasons: List[str] = []
    if saturated:
        reasons.append("fit_pass_rate_high")
        reasons.append("pass_rate_delta_large")
        reasons.append("candidate_status_change_ratio_large")

    return {
        "label": str(case_row.get("label", "")),
        "candidate_count": int(candidate_count),
        "baseline_pass_rate": float(baseline_pass_rate),
        "fit_pass_rate": float(fit_pass_rate),
        "pass_rate_delta": float(pass_rate_delta),
        "candidate_pass_status_changed": int(changed_count),
        "candidate_pass_status_change_ratio": float(change_ratio),
        "criteria": criteria,
        "saturated": bool(saturated),
        "reasons": reasons,
    }


def main() -> None:
    args = parse_args()
    if int(args.min_baseline_candidate_count) <= 0:
        raise ValueError("--min-baseline-candidate-count must be positive")
    if not (0.0 <= float(args.high_pass_rate_threshold) <= 1.0):
        raise ValueError("--high-pass-rate-threshold must be in [0,1]")
    if float(args.large_pass_rate_delta_threshold) < 0.0:
        raise ValueError("--large-pass-rate-delta-threshold must be >= 0")
    if not (0.0 <= float(args.pass_status_change_ratio_threshold) <= 1.0):
        raise ValueError("--pass-status-change-ratio-threshold must be in [0,1]")
    if int(args.max_allowed_saturated_cases) < 0:
        raise ValueError("--max-allowed-saturated-cases must be >= 0")

    batch_summary_json = Path(args.batch_summary_json).expanduser().resolve()
    output_json = Path(args.output_json).expanduser().resolve()
    if not batch_summary_json.exists() or not batch_summary_json.is_file():
        raise FileNotFoundError(f"batch summary not found: {batch_summary_json}")

    payload = _load_json(batch_summary_json)
    cases = payload.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("batch summary missing 'cases' list")

    per_case: List[Dict[str, Any]] = []
    for row in cases:
        if not isinstance(row, Mapping):
            continue
        per_case.append(
            _detect_case_saturation(
                case_row=row,
                min_baseline_candidate_count=int(args.min_baseline_candidate_count),
                high_pass_rate_threshold=float(args.high_pass_rate_threshold),
                large_pass_rate_delta_threshold=float(args.large_pass_rate_delta_threshold),
                pass_status_change_ratio_threshold=float(args.pass_status_change_ratio_threshold),
            )
        )

    saturated_count = int(sum(1 for x in per_case if bool(x.get("saturated", False))))
    gate_failed = bool(saturated_count > int(args.max_allowed_saturated_cases))
    recommendation = (
        "proxy_strength_review_required"
        if gate_failed
        else "proxy_strength_within_expected_range"
    )

    result = {
        "version": 1,
        "input_batch_summary_json": str(batch_summary_json),
        "thresholds": {
            "min_baseline_candidate_count": int(args.min_baseline_candidate_count),
            "high_pass_rate_threshold": float(args.high_pass_rate_threshold),
            "large_pass_rate_delta_threshold": float(args.large_pass_rate_delta_threshold),
            "pass_status_change_ratio_threshold": float(args.pass_status_change_ratio_threshold),
            "max_allowed_saturated_cases": int(args.max_allowed_saturated_cases),
        },
        "case_count": int(len(per_case)),
        "saturated_case_count": int(saturated_count),
        "gate_failed": bool(gate_failed),
        "recommendation": recommendation,
        "cases": per_case,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("Fit-aware replay saturation analysis completed.")
    print(f"  case_count: {result['case_count']}")
    print(f"  saturated_case_count: {result['saturated_case_count']}")
    print(f"  gate_failed: {result['gate_failed']}")
    print(f"  output_json: {output_json}")


if __name__ == "__main__":
    main()
