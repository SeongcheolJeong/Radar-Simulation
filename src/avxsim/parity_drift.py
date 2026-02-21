import json
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import numpy as np


def load_replay_report_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("replay report must be JSON object")
    if "cases" not in payload or not isinstance(payload["cases"], list):
        raise ValueError("replay report missing cases")
    return payload


def build_parity_drift_report(
    reports: Sequence[Mapping[str, Any]],
    quantiles: Sequence[float] = (0.5, 0.9, 0.99),
) -> Dict[str, Any]:
    if len(reports) < 1:
        raise ValueError("at least one report is required")
    q = [float(x) for x in quantiles]
    for x in q:
        if x <= 0 or x >= 1:
            raise ValueError("quantiles must be in (0, 1)")

    scenario_rows = []
    for row in reports:
        name = str(row.get("name", "")).strip()
        if name == "":
            raise ValueError("report entry missing name")
        payload = row.get("report", None)
        if not isinstance(payload, Mapping):
            raise ValueError(f"report entry '{name}' missing report object")
        scenario_rows.append(_summarize_one(name=name, report=payload, quantiles=q))

    baseline = scenario_rows[0]
    drift_rows = []
    for row in scenario_rows[1:]:
        drift_rows.append(_compute_drift_row(baseline=baseline, candidate=row))

    return {
        "version": 1,
        "quantiles": q,
        "baseline": baseline["name"],
        "scenarios": scenario_rows,
        "drift_vs_baseline": drift_rows,
    }


def save_parity_drift_report_json(out_json: str, payload: Mapping[str, Any]) -> None:
    Path(out_json).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _summarize_one(name: str, report: Mapping[str, Any], quantiles: Sequence[float]) -> Dict[str, Any]:
    cases = report.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError(f"report '{name}' has invalid cases")

    metric_values: Dict[str, list] = {}
    candidate_count = 0
    pass_count = 0
    for case in cases:
        cands = case.get("candidates", [])
        if not isinstance(cands, list):
            continue
        for cand in cands:
            candidate_count += 1
            if bool(cand.get("pass", False)):
                pass_count += 1
            metrics = cand.get("metrics", {})
            if not isinstance(metrics, Mapping):
                continue
            for key, value in metrics.items():
                metric_values.setdefault(str(key), []).append(float(value))

    qkeys = [f"q{int(round(x * 100)):02d}" for x in quantiles]
    metric_quantiles: Dict[str, Dict[str, float]] = {}
    for metric, values in metric_values.items():
        arr = np.asarray(values, dtype=np.float64)
        metric_quantiles[metric] = {
            k: float(np.quantile(arr, qv))
            for k, qv in zip(qkeys, quantiles)
        }

    return {
        "name": name,
        "candidate_count": int(candidate_count),
        "pass_count": int(pass_count),
        "pass_rate": 0.0 if candidate_count == 0 else float(pass_count) / float(candidate_count),
        "metric_quantiles": metric_quantiles,
    }


def _compute_drift_row(baseline: Mapping[str, Any], candidate: Mapping[str, Any]) -> Dict[str, Any]:
    bq = baseline.get("metric_quantiles", {})
    cq = candidate.get("metric_quantiles", {})
    if not isinstance(bq, Mapping) or not isinstance(cq, Mapping):
        raise ValueError("invalid metric_quantiles in scenario summary")

    eps = 1e-12
    by_metric = {}
    for metric in sorted(set(bq.keys()) & set(cq.keys())):
        b = bq[metric]
        c = cq[metric]
        if not isinstance(b, Mapping) or not isinstance(c, Mapping):
            continue
        qset = sorted(set(b.keys()) & set(c.keys()))
        item = {}
        for qk in qset:
            bv = float(b[qk])
            cv = float(c[qk])
            item[qk] = {
                "baseline": bv,
                "candidate": cv,
                "delta": cv - bv,
                "ratio": cv / (bv + eps),
            }
        by_metric[str(metric)] = item

    return {
        "baseline": str(baseline.get("name", "")),
        "candidate": str(candidate.get("name", "")),
        "pass_rate_delta": float(candidate.get("pass_rate", 0.0)) - float(baseline.get("pass_rate", 0.0)),
        "metric_drift": by_metric,
    }
