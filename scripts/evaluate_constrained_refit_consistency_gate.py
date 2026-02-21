#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Evaluate constrained-refit preset results and apply multi-case consistency gate "
            "for deterministic adopt/fallback decision."
        )
    )
    p.add_argument("--constrained-summary-json", required=True)
    p.add_argument("--output-json", required=True)
    p.add_argument("--allow-exploratory-recommendation", action="store_true")
    p.add_argument("--require-policy-gate-pass", action="store_true")
    p.add_argument("--max-total-pass-rate-drop", type=float, default=0.0)
    p.add_argument("--max-total-pass-count-drop-ratio", type=float, default=0.0)
    p.add_argument("--max-total-fail-count-increase-ratio", type=float, default=0.0)
    p.add_argument("--max-metric-drift-mean", type=float, default=0.1)
    p.add_argument("--fallback-mode", choices=["baseline_no_fit"], default="baseline_no_fit")
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


def _status_rank(rec: str) -> int:
    r = str(rec)
    if r == "adopt_selected_fit_by_drift_objective":
        return 0
    if r == "exploratory_fit_candidate_selected_by_drift":
        return 1
    if r == "fallback_to_baseline_no_fit":
        return 2
    return 3


def _row_sort_key(row: Mapping[str, Any]) -> Tuple[float, float, float]:
    return (
        float(_status_rank(str(row.get("selection_recommendation", "")))),
        _as_float(row.get("selected_aggregate_score", math.inf), default=math.inf),
        float(_as_int(row.get("preset_index", 1_000_000), default=1_000_000)),
    )


def _gate_row(
    row: Mapping[str, Any],
    allow_exploratory_recommendation: bool,
    require_policy_gate_pass: bool,
    max_total_pass_rate_drop: float,
    max_total_pass_count_drop_ratio: float,
    max_total_fail_count_increase_ratio: float,
    max_metric_drift_mean: float,
) -> Dict[str, Any]:
    reasons: List[str] = []

    preset = str(row.get("preset", ""))
    rec = str(row.get("selection_recommendation", ""))
    search_ok = bool(row.get("search_ok", False))
    selection_mode = str(row.get("selection_mode", ""))
    search_summary_json = Path(str(row.get("search_summary_json", ""))).expanduser().resolve()
    selected_fit_json = row.get("selected_fit_json", None)
    aggregate_score = _as_float(row.get("selected_aggregate_score", math.inf), default=math.inf)

    if not search_ok:
        reasons.append("search_not_ok")
    if selection_mode != "fit":
        reasons.append("selection_mode_not_fit")
    if rec == "adopt_selected_fit_by_drift_objective":
        pass
    elif rec == "exploratory_fit_candidate_selected_by_drift" and allow_exploratory_recommendation:
        pass
    else:
        reasons.append("recommendation_not_allowed")
    if not search_summary_json.exists():
        reasons.append("search_summary_missing")

    case_count = 0
    coverage_count = 0
    pass_rate_drop = math.inf
    pass_count_drop_ratio = math.inf
    fail_count_increase_ratio = math.inf
    metric_drift_mean = math.inf
    policy_gate_failed = None
    policy_gate_recommendation = None

    if search_summary_json.exists():
        search = _load_json(search_summary_json)
        case_count = _as_int(search.get("case_count", 0), default=0)

        policy = search.get("policy_gate", {})
        if isinstance(policy, Mapping):
            policy_gate_failed = bool(policy.get("gate_failed", True))
            policy_gate_recommendation = str(policy.get("recommendation", ""))
        if bool(require_policy_gate_pass) and bool(policy_gate_failed):
            reasons.append("policy_gate_failed")

        sel = search.get("selection", {})
        if not isinstance(sel, Mapping):
            sel = {}
        selected = sel.get("selected_fit_summary", {})
        if not isinstance(selected, Mapping):
            selected = {}
        coverage_count = _as_int(selected.get("coverage_count", 0), default=0)
        pass_rate_drop = _as_float(selected.get("total_pass_rate_drop", math.inf), default=math.inf)
        pass_count_drop_ratio = _as_float(
            selected.get("total_pass_count_drop_ratio", math.inf), default=math.inf
        )
        fail_count_increase_ratio = _as_float(
            selected.get("total_fail_count_increase_ratio", math.inf), default=math.inf
        )
        metric_drift_mean = _as_float(selected.get("metric_drift_mean", math.inf), default=math.inf)

        if case_count <= 0:
            reasons.append("invalid_case_count")
        if coverage_count < case_count:
            reasons.append("incomplete_case_coverage")
        if pass_rate_drop > float(max_total_pass_rate_drop):
            reasons.append("pass_rate_drop_exceeds_limit")
        if pass_count_drop_ratio > float(max_total_pass_count_drop_ratio):
            reasons.append("pass_count_drop_ratio_exceeds_limit")
        if fail_count_increase_ratio > float(max_total_fail_count_increase_ratio):
            reasons.append("fail_count_increase_ratio_exceeds_limit")
        if metric_drift_mean > float(max_metric_drift_mean):
            reasons.append("metric_drift_mean_exceeds_limit")

    return {
        "preset": preset,
        "selection_recommendation": rec,
        "selection_mode": selection_mode,
        "search_ok": search_ok,
        "search_summary_json": str(search_summary_json),
        "selected_fit_json": selected_fit_json,
        "selected_aggregate_score": aggregate_score,
        "case_count": int(case_count),
        "coverage_count": int(coverage_count),
        "total_pass_rate_drop": float(pass_rate_drop),
        "total_pass_count_drop_ratio": float(pass_count_drop_ratio),
        "total_fail_count_increase_ratio": float(fail_count_increase_ratio),
        "metric_drift_mean": float(metric_drift_mean),
        "policy_gate_failed": policy_gate_failed,
        "policy_gate_recommendation": policy_gate_recommendation,
        "eligible": bool(len(reasons) == 0),
        "reasons": sorted(set(reasons)),
    }


def main() -> None:
    args = parse_args()
    if float(args.max_total_pass_rate_drop) < 0.0:
        raise ValueError("--max-total-pass-rate-drop must be >= 0")
    if float(args.max_total_pass_count_drop_ratio) < 0.0:
        raise ValueError("--max-total-pass-count-drop-ratio must be >= 0")
    if float(args.max_total_fail_count_increase_ratio) < 0.0:
        raise ValueError("--max-total-fail-count-increase-ratio must be >= 0")
    if float(args.max_metric_drift_mean) < 0.0:
        raise ValueError("--max-metric-drift-mean must be >= 0")

    constrained_summary_json = Path(args.constrained_summary_json).expanduser().resolve()
    output_json = Path(args.output_json).expanduser().resolve()
    if not constrained_summary_json.exists() or not constrained_summary_json.is_file():
        raise FileNotFoundError(f"constrained summary not found: {constrained_summary_json}")

    constrained = _load_json(constrained_summary_json)
    rows_raw = constrained.get("rows", [])
    if not isinstance(rows_raw, list):
        raise ValueError("constrained summary missing rows list")

    gated_rows: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows_raw):
        if not isinstance(row, Mapping):
            continue
        x = dict(row)
        x["preset_index"] = int(idx)
        gated = _gate_row(
            row=x,
            allow_exploratory_recommendation=bool(args.allow_exploratory_recommendation),
            require_policy_gate_pass=bool(args.require_policy_gate_pass),
            max_total_pass_rate_drop=float(args.max_total_pass_rate_drop),
            max_total_pass_count_drop_ratio=float(args.max_total_pass_count_drop_ratio),
            max_total_fail_count_increase_ratio=float(args.max_total_fail_count_increase_ratio),
            max_metric_drift_mean=float(args.max_metric_drift_mean),
        )
        gated_rows.append(gated)

    eligible_rows = [x for x in gated_rows if bool(x.get("eligible", False))]
    selected = sorted(eligible_rows, key=_row_sort_key)[0] if len(eligible_rows) > 0 else None
    gate_failed = selected is None

    if gate_failed:
        recommendation = "fallback_to_baseline_no_fit"
        selection_mode = str(args.fallback_mode)
        selected_preset = None
        selected_fit_json = None
    else:
        recommendation = "adopt_best_constrained_preset"
        selection_mode = "fit"
        selected_preset = str(selected.get("preset", ""))
        selected_fit_json = selected.get("selected_fit_json", None)

    out = {
        "version": 1,
        "input_constrained_summary_json": str(constrained_summary_json),
        "constraints": {
            "allow_exploratory_recommendation": bool(args.allow_exploratory_recommendation),
            "require_policy_gate_pass": bool(args.require_policy_gate_pass),
            "max_total_pass_rate_drop": float(args.max_total_pass_rate_drop),
            "max_total_pass_count_drop_ratio": float(args.max_total_pass_count_drop_ratio),
            "max_total_fail_count_increase_ratio": float(args.max_total_fail_count_increase_ratio),
            "max_metric_drift_mean": float(args.max_metric_drift_mean),
            "fallback_mode": str(args.fallback_mode),
        },
        "preset_count": int(len(gated_rows)),
        "eligible_preset_count": int(len(eligible_rows)),
        "gate_failed": bool(gate_failed),
        "recommendation": recommendation,
        "selection_mode": selection_mode,
        "selected_preset": selected_preset,
        "selected_fit_json": selected_fit_json,
        "selected": selected,
        "rows": gated_rows,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("Constrained refit consistency gate evaluation completed.")
    print(f"  preset_count: {out['preset_count']}")
    print(f"  eligible_preset_count: {out['eligible_preset_count']}")
    print(f"  gate_failed: {out['gate_failed']}")
    print(f"  recommendation: {out['recommendation']}")
    print(f"  selected_preset: {out['selected_preset']}")
    print(f"  output_json: {output_json}")


if __name__ == "__main__":
    main()
