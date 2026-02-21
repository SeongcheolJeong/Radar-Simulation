#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from avxsim.parity_drift import build_parity_drift_report, load_replay_report_json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Evaluate cross-family parity shift between baseline and tuned replay reports "
            "(family A vs family B)."
        )
    )
    p.add_argument("--baseline-a", required=True, help="label=path replay report for baseline family A")
    p.add_argument("--baseline-b", required=True, help="label=path replay report for baseline family B")
    p.add_argument("--tuned-a", required=True, help="label=path replay report for tuned family A")
    p.add_argument("--tuned-b", required=True, help="label=path replay report for tuned family B")
    p.add_argument(
        "--metric",
        action="append",
        default=None,
        help="Metric to track (repeatable). Default: ra_shape_nmse,rd_shape_nmse",
    )
    p.add_argument("--quantiles", default="0.5,0.9,0.99")
    p.add_argument("--output-json", required=True)
    return p.parse_args()


def _parse_label_path(text: str) -> Tuple[str, str]:
    s = str(text)
    if "=" not in s:
        raise ValueError("argument must be label=path")
    label, path = s.split("=", 1)
    label = label.strip()
    path = path.strip()
    if label == "" or path == "":
        raise ValueError("label/path must be non-empty")
    return label, path


def _parse_quantiles(text: str) -> List[float]:
    parts = [x.strip() for x in str(text).split(",")]
    out = [float(x) for x in parts if x != ""]
    if len(out) == 0:
        raise ValueError("quantiles must contain at least one value")
    for q in out:
        if q <= 0 or q >= 1:
            raise ValueError("quantiles must be in (0, 1)")
    return out


def _qkeys(quantiles: Sequence[float]) -> List[str]:
    return [f"q{int(round(float(q) * 100)):02d}" for q in quantiles]


def _summarize_one(label: str, path: str, quantiles: Sequence[float]) -> Dict[str, Any]:
    payload = load_replay_report_json(path)
    report = build_parity_drift_report(
        reports=[{"name": label, "report": payload}],
        quantiles=quantiles,
    )
    return report["scenarios"][0]


def _cross_gap(
    summary_a: Mapping[str, Any],
    summary_b: Mapping[str, Any],
    metrics: Sequence[str],
    quantiles: Sequence[float],
) -> Dict[str, Dict[str, float]]:
    qa = summary_a.get("metric_quantiles", {})
    qb = summary_b.get("metric_quantiles", {})
    if not isinstance(qa, Mapping) or not isinstance(qb, Mapping):
        raise ValueError("invalid metric_quantiles")

    out: Dict[str, Dict[str, float]] = {}
    eps = 1e-12
    qnames = _qkeys(quantiles)
    for metric in metrics:
        a_row = qa.get(metric, None)
        b_row = qb.get(metric, None)
        if not isinstance(a_row, Mapping) or not isinstance(b_row, Mapping):
            continue
        metric_row: Dict[str, float] = {}
        for qn in qnames:
            if qn not in a_row or qn not in b_row:
                continue
            av = float(a_row[qn])
            bv = float(b_row[qn])
            metric_row[f"{qn}_family_a"] = av
            metric_row[f"{qn}_family_b"] = bv
            metric_row[f"{qn}_gap_abs"] = abs(bv - av)
            metric_row[f"{qn}_gap_signed"] = bv - av
            metric_row[f"{qn}_ratio_b_over_a"] = bv / (av + eps)
        out[str(metric)] = metric_row
    return out


def _improvement(
    baseline_gap: Mapping[str, Dict[str, float]],
    tuned_gap: Mapping[str, Dict[str, float]],
    quantiles: Sequence[float],
) -> Dict[str, Dict[str, float]]:
    eps = 1e-12
    out: Dict[str, Dict[str, float]] = {}
    qnames = _qkeys(quantiles)
    for metric in sorted(set(baseline_gap.keys()) & set(tuned_gap.keys())):
        brow = baseline_gap[metric]
        trow = tuned_gap[metric]
        mrow: Dict[str, float] = {}
        for qn in qnames:
            bk = f"{qn}_gap_abs"
            if bk not in brow or bk not in trow:
                continue
            b = float(brow[bk])
            t = float(trow[bk])
            mrow[f"{qn}_baseline_gap_abs"] = b
            mrow[f"{qn}_tuned_gap_abs"] = t
            mrow[f"{qn}_gap_reduction_abs"] = b - t
            mrow[f"{qn}_tuned_over_baseline_gap"] = t / (b + eps)
        out[metric] = mrow
    return out


def main() -> None:
    args = parse_args()
    quantiles = _parse_quantiles(args.quantiles)
    metrics = args.metric if args.metric else ["ra_shape_nmse", "rd_shape_nmse"]

    b_label_a, b_path_a = _parse_label_path(args.baseline_a)
    b_label_b, b_path_b = _parse_label_path(args.baseline_b)
    t_label_a, t_path_a = _parse_label_path(args.tuned_a)
    t_label_b, t_path_b = _parse_label_path(args.tuned_b)

    baseline_a = _summarize_one(b_label_a, b_path_a, quantiles)
    baseline_b = _summarize_one(b_label_b, b_path_b, quantiles)
    tuned_a = _summarize_one(t_label_a, t_path_a, quantiles)
    tuned_b = _summarize_one(t_label_b, t_path_b, quantiles)

    baseline_gap = _cross_gap(baseline_a, baseline_b, metrics=metrics, quantiles=quantiles)
    tuned_gap = _cross_gap(tuned_a, tuned_b, metrics=metrics, quantiles=quantiles)
    improvement = _improvement(baseline_gap, tuned_gap, quantiles=quantiles)

    baseline_pass_rate_gap_abs = abs(float(baseline_b["pass_rate"]) - float(baseline_a["pass_rate"]))
    tuned_pass_rate_gap_abs = abs(float(tuned_b["pass_rate"]) - float(tuned_a["pass_rate"]))

    payload = {
        "version": 1,
        "metrics": list(metrics),
        "quantiles": list(quantiles),
        "families": {
            "family_a": {
                "baseline": {"label": b_label_a, "path": str(b_path_a)},
                "tuned": {"label": t_label_a, "path": str(t_path_a)},
            },
            "family_b": {
                "baseline": {"label": b_label_b, "path": str(b_path_b)},
                "tuned": {"label": t_label_b, "path": str(t_path_b)},
            },
        },
        "summaries": {
            "baseline": {"family_a": baseline_a, "family_b": baseline_b},
            "tuned": {"family_a": tuned_a, "family_b": tuned_b},
        },
        "cross_family_gap": {
            "baseline": baseline_gap,
            "tuned": tuned_gap,
            "improvement": improvement,
        },
        "pass_rate_gap": {
            "baseline_abs": baseline_pass_rate_gap_abs,
            "tuned_abs": tuned_pass_rate_gap_abs,
            "reduction_abs": baseline_pass_rate_gap_abs - tuned_pass_rate_gap_abs,
            "tuned_over_baseline": tuned_pass_rate_gap_abs / (baseline_pass_rate_gap_abs + 1e-12),
        },
    }

    out = Path(args.output_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("Cross-family parity shift evaluation completed.")
    print(f"  metrics: {','.join(metrics)}")
    print(f"  quantiles: {','.join([str(x) for x in quantiles])}")
    print(f"  baseline_pass_rate_gap_abs: {baseline_pass_rate_gap_abs:.6f}")
    print(f"  tuned_pass_rate_gap_abs: {tuned_pass_rate_gap_abs:.6f}")
    print(f"  output_json: {args.output_json}")


if __name__ == "__main__":
    main()
