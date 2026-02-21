#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Evaluate fit-aware measured replay batch summary under adoption policy "
            "(non-degradation constraints + minimum improvement count)."
        )
    )
    p.add_argument("--batch-summary-json", required=True)
    p.add_argument("--output-json", required=True)
    p.add_argument(
        "--require-non-degradation-all-cases",
        action="store_true",
        help="If set, gate fails when any case has no non-degrading attempt.",
    )
    p.add_argument(
        "--max-pass-rate-drop",
        type=float,
        default=0.0,
        help="Allowed drop from baseline pass_rate (absolute).",
    )
    p.add_argument(
        "--max-pass-count-drop",
        type=int,
        default=0,
        help="Allowed drop from baseline pass_count.",
    )
    p.add_argument(
        "--max-fail-count-increase",
        type=int,
        default=0,
        help="Allowed increase from baseline fail_count.",
    )
    p.add_argument(
        "--min-improved-cases",
        type=int,
        default=1,
        help="Minimum number of improved cases required for adoption.",
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


def _is_non_degrading(
    delta: Mapping[str, Any],
    max_pass_rate_drop: float,
    max_pass_count_drop: int,
    max_fail_count_increase: int,
) -> Tuple[bool, List[str]]:
    pass_delta = _as_int(delta.get("pass_count_delta", 0))
    fail_delta = _as_int(delta.get("fail_count_delta", 0))
    pass_rate_delta = _as_float(delta.get("pass_rate_delta", 0.0))

    reasons: List[str] = []
    if pass_rate_delta < -float(max_pass_rate_drop):
        reasons.append("pass_rate_drop_exceeds_limit")
    if pass_delta < -int(max_pass_count_drop):
        reasons.append("pass_count_drop_exceeds_limit")
    if fail_delta > int(max_fail_count_increase):
        reasons.append("fail_count_increase_exceeds_limit")
    return (len(reasons) == 0), reasons


def _attempt_sort_key(attempt: Mapping[str, Any]) -> Tuple[float, float]:
    delta = attempt.get("delta", {})
    return (
        _as_float(delta.get("pass_count_delta", 0.0)),
        _as_float(delta.get("pass_rate_delta", 0.0)),
    )


def _case_policy_eval(
    case_row: Mapping[str, Any],
    max_pass_rate_drop: float,
    max_pass_count_drop: int,
    max_fail_count_increase: int,
) -> Dict[str, Any]:
    label = str(case_row.get("label", ""))
    baseline = case_row.get("baseline_summary", {})
    attempts_raw = case_row.get("attempts", [])
    attempts = attempts_raw if isinstance(attempts_raw, list) else []

    eligible: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    for a in attempts:
        if not isinstance(a, Mapping):
            continue
        delta = a.get("delta", {})
        if not isinstance(delta, Mapping):
            delta = {}
        ok, reasons = _is_non_degrading(
            delta=delta,
            max_pass_rate_drop=float(max_pass_rate_drop),
            max_pass_count_drop=int(max_pass_count_drop),
            max_fail_count_increase=int(max_fail_count_increase),
        )
        row = {
            "attempt_index": _as_int(a.get("attempt_index", -1)),
            "attempt_id": str(a.get("attempt_id", "")),
            "fit_json": str(a.get("fit_json", "")),
            "delta": {
                "pass_count_delta": _as_float(delta.get("pass_count_delta", 0.0)),
                "fail_count_delta": _as_float(delta.get("fail_count_delta", 0.0)),
                "pass_rate_delta": _as_float(delta.get("pass_rate_delta", 0.0)),
            },
            "non_degrading": bool(ok),
            "reasons": reasons,
            "gain": bool(_is_gain(delta)),
        }
        if ok:
            eligible.append(row)
        else:
            rejected.append(row)

    best_eligible: Optional[Dict[str, Any]] = None
    if len(eligible) > 0:
        best_eligible = sorted(eligible, key=_attempt_sort_key, reverse=True)[0]

    status: str
    if best_eligible is None:
        status = "degrade_only"
    elif bool(best_eligible["gain"]):
        status = "improved_within_policy"
    else:
        status = "non_degrading_no_gain"

    return {
        "label": label,
        "baseline_summary": baseline,
        "attempt_count": int(len(attempts)),
        "eligible_attempt_count": int(len(eligible)),
        "rejected_attempt_count": int(len(rejected)),
        "status": status,
        "best_eligible_attempt": best_eligible,
        "eligible_attempts": eligible,
        "rejected_attempts": rejected,
    }


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

    batch = _load_json(batch_summary_json)
    cases_raw = batch.get("cases", [])
    if not isinstance(cases_raw, list):
        raise ValueError("batch summary missing 'cases' list")

    cases: List[Dict[str, Any]] = []
    for row in cases_raw:
        if not isinstance(row, Mapping):
            continue
        cases.append(
            _case_policy_eval(
                case_row=row,
                max_pass_rate_drop=float(args.max_pass_rate_drop),
                max_pass_count_drop=int(args.max_pass_count_drop),
                max_fail_count_increase=int(args.max_fail_count_increase),
            )
        )

    improved_case_count = int(sum(1 for x in cases if x.get("status") == "improved_within_policy"))
    degrade_only_case_count = int(sum(1 for x in cases if x.get("status") == "degrade_only"))
    non_degrading_case_count = int(len(cases) - degrade_only_case_count)

    gate_failed_non_degradation = bool(
        bool(args.require_non_degradation_all_cases) and degrade_only_case_count > 0
    )
    gate_failed_min_improvement = bool(improved_case_count < int(args.min_improved_cases))
    gate_failed = bool(gate_failed_non_degradation or gate_failed_min_improvement)

    if gate_failed_non_degradation:
        recommendation = "reject_fit_lock_due_to_degradation"
    elif gate_failed_min_improvement:
        recommendation = "hold_fit_lock_no_material_gain"
    else:
        recommendation = "accept_fit_lock"

    out = {
        "version": 1,
        "input_batch_summary_json": str(batch_summary_json),
        "batch_metadata": {
            "baseline_mode": str(batch.get("baseline_mode", "")),
            "fit_jsons": list(batch.get("fit_jsons", []))
            if isinstance(batch.get("fit_jsons", []), list)
            else [],
        },
        "policy": {
            "require_non_degradation_all_cases": bool(args.require_non_degradation_all_cases),
            "max_pass_rate_drop": float(args.max_pass_rate_drop),
            "max_pass_count_drop": int(args.max_pass_count_drop),
            "max_fail_count_increase": int(args.max_fail_count_increase),
            "min_improved_cases": int(args.min_improved_cases),
        },
        "case_count": int(len(cases)),
        "non_degrading_case_count": int(non_degrading_case_count),
        "degrade_only_case_count": int(degrade_only_case_count),
        "improved_case_count": int(improved_case_count),
        "gate_failed": bool(gate_failed),
        "gate_failed_non_degradation": bool(gate_failed_non_degradation),
        "gate_failed_min_improvement": bool(gate_failed_min_improvement),
        "recommendation": recommendation,
        "cases": cases,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("Fit-aware replay policy gate evaluation completed.")
    print(f"  case_count: {out['case_count']}")
    print(f"  improved_case_count: {out['improved_case_count']}")
    print(f"  degrade_only_case_count: {out['degrade_only_case_count']}")
    print(f"  gate_failed: {out['gate_failed']}")
    print(f"  recommendation: {out['recommendation']}")
    print(f"  output_json: {output_json}")


if __name__ == "__main__":
    main()
