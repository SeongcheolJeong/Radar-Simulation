#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from avxsim.parity_drift import build_parity_drift_report, load_replay_report_json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Select measured replay fit lock by drift objective (for saturated baseline mode) "
            "using per-fit aggregate pass/fail deltas and parity-metric drift penalties."
        )
    )
    p.add_argument("--batch-summary-json", required=True)
    p.add_argument("--output-json", required=True)

    p.add_argument("--metric", action="append", default=["ra_shape_nmse", "rd_shape_nmse"])
    p.add_argument("--drift-quantile", type=float, default=0.9)

    p.add_argument("--weight-pass-rate-drop", type=float, default=100.0)
    p.add_argument("--weight-pass-count-drop-ratio", type=float, default=20.0)
    p.add_argument("--weight-fail-count-increase-ratio", type=float, default=20.0)
    p.add_argument("--weight-metric-drift", type=float, default=1.0)

    p.add_argument("--max-pass-rate-drop", type=float, default=1.0)
    p.add_argument("--max-pass-count-drop-ratio", type=float, default=1.0)
    p.add_argument("--max-fail-count-increase-ratio", type=float, default=1.0)
    p.add_argument("--max-metric-drift", type=float, default=1e9)
    p.add_argument("--require-full-case-coverage", action="store_true")

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


def _collect_fit_jsons(cases: Sequence[Mapping[str, Any]]) -> List[str]:
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


def _quantile_key(q: float) -> str:
    return f"q{int(round(float(q) * 100)):02d}"


def _calc_metric_drift_penalty(
    baseline_report_json: Path,
    candidate_report_json: Path,
    metrics: Sequence[str],
    drift_quantile: float,
) -> Tuple[float, Dict[str, float], List[str]]:
    errors: List[str] = []
    if not baseline_report_json.exists():
        return math.inf, {}, ["baseline_report_missing"]
    if not candidate_report_json.exists():
        return math.inf, {}, ["candidate_report_missing"]

    base = load_replay_report_json(str(baseline_report_json))
    cand = load_replay_report_json(str(candidate_report_json))
    payload = build_parity_drift_report(
        reports=[
            {"name": "baseline", "report": base},
            {"name": "candidate", "report": cand},
        ],
        quantiles=[float(drift_quantile)],
    )
    drift_rows = payload.get("drift_vs_baseline", [])
    if not isinstance(drift_rows, list) or len(drift_rows) == 0:
        return math.inf, {}, ["drift_payload_missing"]
    drift = drift_rows[0].get("metric_drift", {})
    if not isinstance(drift, Mapping):
        return math.inf, {}, ["drift_metric_missing"]

    qk = _quantile_key(drift_quantile)
    penalties: Dict[str, float] = {}
    for metric in metrics:
        mrow = drift.get(str(metric), None)
        if not isinstance(mrow, Mapping):
            errors.append(f"metric_missing:{metric}")
            continue
        qrow = mrow.get(qk, None)
        if not isinstance(qrow, Mapping):
            errors.append(f"quantile_missing:{metric}:{qk}")
            continue
        ratio = _as_float(qrow.get("ratio", None), default=math.inf)
        if not math.isfinite(ratio):
            errors.append(f"ratio_invalid:{metric}:{qk}")
            continue
        penalties[str(metric)] = abs(float(ratio) - 1.0)

    if len(penalties) == 0:
        return math.inf, penalties, (errors if len(errors) > 0 else ["metric_penalty_empty"])
    return float(sum(penalties.values()) / float(len(penalties))), penalties, errors


def _fit_sort_key(row: Mapping[str, Any]) -> Tuple[float, float, float]:
    return (
        -_as_float(row.get("aggregate_score", math.inf), default=math.inf),
        -_as_float(row.get("metric_drift_mean", math.inf), default=math.inf),
        _as_float(row.get("total_pass_rate_drop", math.inf), default=math.inf),
    )


def main() -> None:
    args = parse_args()
    if not (0.0 < float(args.drift_quantile) < 1.0):
        raise ValueError("--drift-quantile must be in (0,1)")
    if _as_float(args.max_pass_rate_drop) < 0.0:
        raise ValueError("--max-pass-rate-drop must be >= 0")
    if _as_float(args.max_pass_count_drop_ratio) < 0.0:
        raise ValueError("--max-pass-count-drop-ratio must be >= 0")
    if _as_float(args.max_fail_count_increase_ratio) < 0.0:
        raise ValueError("--max-fail-count-increase-ratio must be >= 0")
    if _as_float(args.max_metric_drift) < 0.0:
        raise ValueError("--max-metric-drift must be >= 0")

    batch_summary_json = Path(args.batch_summary_json).expanduser().resolve()
    output_json = Path(args.output_json).expanduser().resolve()
    if not batch_summary_json.exists() or not batch_summary_json.is_file():
        raise FileNotFoundError(f"batch summary not found: {batch_summary_json}")

    payload = _load_json(batch_summary_json)
    cases_raw = payload.get("cases", [])
    if not isinstance(cases_raw, list):
        raise ValueError("batch summary missing 'cases' list")
    cases: List[Mapping[str, Any]] = [x for x in cases_raw if isinstance(x, Mapping)]

    metrics = [str(m) for m in args.metric if str(m).strip() != ""]
    if len(metrics) == 0:
        raise ValueError("at least one --metric is required")

    fit_jsons = _collect_fit_jsons(cases)
    fit_rows: List[Dict[str, Any]] = []
    case_count = int(len(cases))

    w_pass_rate = float(args.weight_pass_rate_drop)
    w_pass_count_ratio = float(args.weight_pass_count_drop_ratio)
    w_fail_ratio = float(args.weight_fail_count_increase_ratio)
    w_metric = float(args.weight_metric_drift)

    for fit_json in fit_jsons:
        coverage_count = 0
        per_case_rows: List[Dict[str, Any]] = []

        pass_rate_drops: List[float] = []
        pass_count_drop_ratios: List[float] = []
        fail_count_increase_ratios: List[float] = []
        metric_drift_penalties: List[float] = []

        rejected_reasons: List[str] = []

        for case_row in cases:
            label = str(case_row.get("label", ""))
            baseline = case_row.get("baseline_summary", {})
            baseline_candidate_count = max(1, _as_int(baseline.get("candidate_count", 0), default=1))

            attempt = _find_attempt_for_fit(case_row, fit_json)
            if attempt is None:
                per_case_rows.append(
                    {
                        "label": label,
                        "evaluated": False,
                        "eligible": False,
                        "reasons": ["fit_not_evaluated_for_case"],
                    }
                )
                continue

            coverage_count += 1
            delta = attempt.get("delta", {})
            if not isinstance(delta, Mapping):
                delta = {}

            pass_rate_drop = max(0.0, -_as_float(delta.get("pass_rate_delta", 0.0)))
            pass_count_drop_ratio = max(0.0, -_as_float(delta.get("pass_count_delta", 0.0))) / float(
                baseline_candidate_count
            )
            fail_count_increase_ratio = max(
                0.0, _as_float(delta.get("fail_count_delta", 0.0))
            ) / float(baseline_candidate_count)

            base_report = Path(str(case_row.get("baseline_replay_report_json", ""))).expanduser().resolve()
            cand_report = Path(str(attempt.get("replay_report_json", ""))).expanduser().resolve()
            metric_penalty, metric_penalties, metric_errors = _calc_metric_drift_penalty(
                baseline_report_json=base_report,
                candidate_report_json=cand_report,
                metrics=metrics,
                drift_quantile=float(args.drift_quantile),
            )

            case_reasons: List[str] = []
            if pass_rate_drop > float(args.max_pass_rate_drop):
                case_reasons.append("pass_rate_drop_exceeds_limit")
            if pass_count_drop_ratio > float(args.max_pass_count_drop_ratio):
                case_reasons.append("pass_count_drop_ratio_exceeds_limit")
            if fail_count_increase_ratio > float(args.max_fail_count_increase_ratio):
                case_reasons.append("fail_count_increase_ratio_exceeds_limit")
            if metric_penalty > float(args.max_metric_drift):
                case_reasons.append("metric_drift_exceeds_limit")
            case_reasons.extend(metric_errors)

            case_eligible = len(case_reasons) == 0
            if not case_eligible:
                rejected_reasons.extend(case_reasons)

            pass_rate_drops.append(float(pass_rate_drop))
            pass_count_drop_ratios.append(float(pass_count_drop_ratio))
            fail_count_increase_ratios.append(float(fail_count_increase_ratio))
            metric_drift_penalties.append(float(metric_penalty))

            per_case_rows.append(
                {
                    "label": label,
                    "evaluated": True,
                    "eligible": bool(case_eligible),
                    "reasons": case_reasons,
                    "delta": {
                        "pass_count_delta": _as_float(delta.get("pass_count_delta", 0.0)),
                        "fail_count_delta": _as_float(delta.get("fail_count_delta", 0.0)),
                        "pass_rate_delta": _as_float(delta.get("pass_rate_delta", 0.0)),
                    },
                    "penalties": {
                        "pass_rate_drop": float(pass_rate_drop),
                        "pass_count_drop_ratio": float(pass_count_drop_ratio),
                        "fail_count_increase_ratio": float(fail_count_increase_ratio),
                        "metric_drift": float(metric_penalty),
                        "metric_penalties": metric_penalties,
                    },
                }
            )

        if bool(args.require_full_case_coverage) and coverage_count < case_count:
            rejected_reasons.append("incomplete_case_coverage")

        if len(pass_rate_drops) == 0:
            mean_pass_rate_drop = math.inf
            mean_pass_count_drop_ratio = math.inf
            mean_fail_count_increase_ratio = math.inf
            mean_metric_drift = math.inf
        else:
            mean_pass_rate_drop = float(sum(pass_rate_drops) / len(pass_rate_drops))
            mean_pass_count_drop_ratio = float(sum(pass_count_drop_ratios) / len(pass_count_drop_ratios))
            mean_fail_count_increase_ratio = float(sum(fail_count_increase_ratios) / len(fail_count_increase_ratios))
            mean_metric_drift = float(sum(metric_drift_penalties) / len(metric_drift_penalties))

        aggregate_score = (
            (w_pass_rate * mean_pass_rate_drop)
            + (w_pass_count_ratio * mean_pass_count_drop_ratio)
            + (w_fail_ratio * mean_fail_count_increase_ratio)
            + (w_metric * mean_metric_drift)
        )

        eligible = bool(len(rejected_reasons) == 0)
        fit_rows.append(
            {
                "fit_json": str(fit_json),
                "case_count": int(case_count),
                "coverage_count": int(coverage_count),
                "eligible": eligible,
                "rejected_reasons": sorted(set(rejected_reasons)),
                "aggregate_score": float(aggregate_score),
                "total_pass_rate_drop": float(sum(pass_rate_drops)),
                "total_pass_count_drop_ratio": float(sum(pass_count_drop_ratios)),
                "total_fail_count_increase_ratio": float(sum(fail_count_increase_ratios)),
                "metric_drift_mean": float(mean_metric_drift),
                "cases": per_case_rows,
            }
        )

    eligible_rows = [x for x in fit_rows if bool(x.get("eligible", False))]
    if len(eligible_rows) > 0:
        selected = sorted(eligible_rows, key=lambda r: _as_float(r.get("aggregate_score", math.inf)))[0]
        selection_mode = "fit"
        selected_fit_json = str(selected.get("fit_json", ""))
        selected_summary = selected
        has_degradation = bool(
            (_as_float(selected.get("total_pass_rate_drop", 0.0)) > 0.0)
            or (_as_float(selected.get("total_pass_count_drop_ratio", 0.0)) > 0.0)
            or (_as_float(selected.get("total_fail_count_increase_ratio", 0.0)) > 0.0)
        )
        recommendation = (
            "exploratory_fit_candidate_selected_by_drift"
            if has_degradation
            else "adopt_selected_fit_by_drift_objective"
        )
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
        "objective": {
            "type": "drift",
            "metrics": metrics,
            "drift_quantile": float(args.drift_quantile),
            "weights": {
                "pass_rate_drop": float(w_pass_rate),
                "pass_count_drop_ratio": float(w_pass_count_ratio),
                "fail_count_increase_ratio": float(w_fail_ratio),
                "metric_drift": float(w_metric),
            },
        },
        "constraints": {
            "max_pass_rate_drop": float(args.max_pass_rate_drop),
            "max_pass_count_drop_ratio": float(args.max_pass_count_drop_ratio),
            "max_fail_count_increase_ratio": float(args.max_fail_count_increase_ratio),
            "max_metric_drift": float(args.max_metric_drift),
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

    print("Measured replay fit-lock drift-objective selection completed.")
    print(f"  case_count: {case_count}")
    print(f"  fit_json_count: {len(fit_jsons)}")
    print(f"  selection_mode: {selection_mode}")
    print(f"  recommendation: {recommendation}")
    print(f"  selected_fit_json: {selected_fit_json}")
    print(f"  output_json: {output_json}")


if __name__ == "__main__":
    main()
