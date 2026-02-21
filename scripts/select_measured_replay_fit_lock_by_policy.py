#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Select a measured replay fit lock from fit-aware batch summary using "
            "non-degradation policy with baseline fallback."
        )
    )
    p.add_argument("--batch-summary-json", required=True)
    p.add_argument("--output-json", required=True)
    p.add_argument("--max-pass-rate-drop", type=float, default=0.0)
    p.add_argument("--max-pass-count-drop", type=int, default=0)
    p.add_argument("--max-fail-count-increase", type=int, default=0)
    p.add_argument("--min-improved-cases", type=int, default=1)
    p.add_argument(
        "--require-full-case-coverage",
        action="store_true",
        help="Reject fit candidates not evaluated on all cases in the batch summary.",
    )
    p.add_argument(
        "--fallback-mode",
        choices=["baseline_no_fit"],
        default="baseline_no_fit",
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


def _is_gain(delta: Mapping[str, Any]) -> bool:
    pass_delta = _as_int(delta.get("pass_count_delta", 0))
    pass_rate_delta = _as_float(delta.get("pass_rate_delta", 0.0))
    return bool((pass_delta > 0) or (pass_delta == 0 and pass_rate_delta > 0.0))


def _non_degrading_reasons(
    delta: Mapping[str, Any],
    max_pass_rate_drop: float,
    max_pass_count_drop: int,
    max_fail_count_increase: int,
) -> List[str]:
    reasons: List[str] = []
    pass_rate_delta = _as_float(delta.get("pass_rate_delta", 0.0))
    pass_count_delta = _as_int(delta.get("pass_count_delta", 0))
    fail_count_delta = _as_int(delta.get("fail_count_delta", 0))
    if pass_rate_delta < -float(max_pass_rate_drop):
        reasons.append("pass_rate_drop_exceeds_limit")
    if pass_count_delta < -int(max_pass_count_drop):
        reasons.append("pass_count_drop_exceeds_limit")
    if fail_count_delta > int(max_fail_count_increase):
        reasons.append("fail_count_increase_exceeds_limit")
    return reasons


def _fit_rank_key(row: Mapping[str, Any]) -> Tuple[float, float, float]:
    return (
        float(row.get("improved_case_count", 0.0)),
        float(row.get("total_pass_count_delta", 0.0)),
        float(row.get("total_pass_rate_delta", 0.0)),
    )


def _collect_fit_candidates(cases: Sequence[Mapping[str, Any]]) -> List[str]:
    out: List[str] = []
    seen = set()
    for c in cases:
        attempts = c.get("attempts", [])
        if not isinstance(attempts, list):
            continue
        for a in attempts:
            if not isinstance(a, Mapping):
                continue
            fit_json = str(a.get("fit_json", "")).strip()
            if fit_json == "" or fit_json in seen:
                continue
            seen.add(fit_json)
            out.append(fit_json)
    return out


def _find_attempt_for_fit(case_row: Mapping[str, Any], fit_json: str) -> Optional[Mapping[str, Any]]:
    attempts = case_row.get("attempts", [])
    if not isinstance(attempts, list):
        return None
    for a in attempts:
        if not isinstance(a, Mapping):
            continue
        if str(a.get("fit_json", "")).strip() == str(fit_json):
            return a
    return None


def main() -> None:
    args = parse_args()
    if float(args.max_pass_rate_drop) < 0.0:
        raise ValueError("--max-pass-rate-drop must be >= 0")
    if int(args.max_pass_count_drop) < 0:
        raise ValueError("--max-pass-count-drop must be >= 0")
    if int(args.max_fail_count_increase) < 0:
        raise ValueError("--max-fail-count-increase must be >= 0")
    if int(args.min_improved_cases) < 0:
        raise ValueError("--min-improved-cases must be >= 0")

    batch_summary_json = Path(args.batch_summary_json).expanduser().resolve()
    output_json = Path(args.output_json).expanduser().resolve()
    if not batch_summary_json.exists() or not batch_summary_json.is_file():
        raise FileNotFoundError(f"batch summary not found: {batch_summary_json}")

    payload = _load_json(batch_summary_json)
    cases_raw = payload.get("cases", [])
    if not isinstance(cases_raw, list):
        raise ValueError("batch summary missing 'cases' list")
    cases: List[Mapping[str, Any]] = [x for x in cases_raw if isinstance(x, Mapping)]

    fit_jsons = _collect_fit_candidates(cases)
    fit_rows: List[Dict[str, Any]] = []
    case_count = int(len(cases))

    for fit_json in fit_jsons:
        coverage_count = 0
        improved_case_count = 0
        non_degrading_case_count = 0
        total_pass_count_delta = 0.0
        total_pass_rate_delta = 0.0
        per_case_rows: List[Dict[str, Any]] = []
        fit_rejected_reasons: List[str] = []

        for case_row in cases:
            label = str(case_row.get("label", ""))
            attempt = _find_attempt_for_fit(case_row, fit_json)
            if attempt is None:
                per_case_rows.append(
                    {
                        "label": label,
                        "evaluated": False,
                        "non_degrading": False,
                        "gain": False,
                        "reasons": ["fit_not_evaluated_for_case"],
                    }
                )
                continue

            coverage_count += 1
            delta = attempt.get("delta", {})
            if not isinstance(delta, Mapping):
                delta = {}
            reasons = _non_degrading_reasons(
                delta=delta,
                max_pass_rate_drop=float(args.max_pass_rate_drop),
                max_pass_count_drop=int(args.max_pass_count_drop),
                max_fail_count_increase=int(args.max_fail_count_increase),
            )
            gain = _is_gain(delta)
            non_degrading = len(reasons) == 0

            if non_degrading:
                non_degrading_case_count += 1
            if gain:
                improved_case_count += 1
            total_pass_count_delta += _as_float(delta.get("pass_count_delta", 0.0))
            total_pass_rate_delta += _as_float(delta.get("pass_rate_delta", 0.0))

            per_case_rows.append(
                {
                    "label": label,
                    "evaluated": True,
                    "non_degrading": bool(non_degrading),
                    "gain": bool(gain),
                    "reasons": reasons,
                    "delta": {
                        "pass_count_delta": _as_float(delta.get("pass_count_delta", 0.0)),
                        "fail_count_delta": _as_float(delta.get("fail_count_delta", 0.0)),
                        "pass_rate_delta": _as_float(delta.get("pass_rate_delta", 0.0)),
                    },
                }
            )

        if bool(args.require_full_case_coverage) and coverage_count < case_count:
            fit_rejected_reasons.append("incomplete_case_coverage")
        if non_degrading_case_count < case_count:
            fit_rejected_reasons.append("degradation_detected")
        if improved_case_count < int(args.min_improved_cases):
            fit_rejected_reasons.append("insufficient_improved_cases")

        fit_rows.append(
            {
                "fit_json": str(fit_json),
                "case_count": int(case_count),
                "coverage_count": int(coverage_count),
                "non_degrading_case_count": int(non_degrading_case_count),
                "improved_case_count": int(improved_case_count),
                "total_pass_count_delta": float(total_pass_count_delta),
                "total_pass_rate_delta": float(total_pass_rate_delta),
                "eligible": bool(len(fit_rejected_reasons) == 0),
                "rejected_reasons": fit_rejected_reasons,
                "cases": per_case_rows,
            }
        )

    eligible_rows = [x for x in fit_rows if bool(x.get("eligible", False))]
    if len(eligible_rows) > 0:
        selected = sorted(eligible_rows, key=_fit_rank_key, reverse=True)[0]
        selection_mode = "fit"
        recommendation = "adopt_selected_fit"
        selected_fit_json = str(selected.get("fit_json", ""))
        selected_summary = selected
    else:
        selection_mode = str(args.fallback_mode)
        recommendation = "fallback_to_baseline_no_fit"
        selected_fit_json = None
        selected_summary = None

    out = {
        "version": 1,
        "input_batch_summary_json": str(batch_summary_json),
        "batch_metadata": {
            "baseline_mode": str(payload.get("baseline_mode", "")),
            "case_count": int(case_count),
            "fit_json_count": int(len(fit_jsons)),
        },
        "policy": {
            "max_pass_rate_drop": float(args.max_pass_rate_drop),
            "max_pass_count_drop": int(args.max_pass_count_drop),
            "max_fail_count_increase": int(args.max_fail_count_increase),
            "min_improved_cases": int(args.min_improved_cases),
            "require_full_case_coverage": bool(args.require_full_case_coverage),
            "fallback_mode": str(args.fallback_mode),
        },
        "selection": {
            "selection_mode": selection_mode,
            "recommendation": recommendation,
            "selected_fit_json": selected_fit_json,
            "selected_fit_summary": selected_summary,
        },
        "fit_candidates": fit_rows,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("Measured replay fit-lock policy selection completed.")
    print(f"  case_count: {case_count}")
    print(f"  fit_json_count: {len(fit_jsons)}")
    print(f"  selection_mode: {selection_mode}")
    print(f"  recommendation: {recommendation}")
    print(f"  selected_fit_json: {selected_fit_json}")
    print(f"  output_json: {output_json}")


if __name__ == "__main__":
    main()
