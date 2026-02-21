import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np

from .adc_pack_builder import load_adc_from_npz, reorder_adc_to_sctr
from .adapters import to_radarsimpy_view


DEFAULT_RADARSIMPY_PERIODIC_THRESHOLDS: Dict[str, float] = {
    "view_nmse_max": 1e-8,
    "power_nmse_max": 1e-8,
    "mean_abs_error_max": 1e-5,
    "max_abs_error_max": 1e-3,
    "complex_corr_abs_min": 0.999,
}


def load_radarsimpy_periodic_manifest_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("periodic manifest json must be object")
    return dict(payload)


def save_radarsimpy_periodic_summary_json(path: str, payload: Mapping[str, Any]) -> None:
    Path(path).write_text(json.dumps(dict(payload), indent=2), encoding="utf-8")


def evaluate_radarsimpy_periodic_manifest(
    manifest_payload: Mapping[str, Any],
    thresholds: Optional[Mapping[str, float]] = None,
) -> Dict[str, Any]:
    cases_raw = manifest_payload.get("cases")
    if not isinstance(cases_raw, Sequence) or isinstance(cases_raw, (str, bytes)):
        raise ValueError("manifest.cases must be list")
    if len(cases_raw) == 0:
        raise ValueError("manifest.cases must be non-empty")

    threshold_map = dict(DEFAULT_RADARSIMPY_PERIODIC_THRESHOLDS)
    if thresholds is not None:
        for k, v in thresholds.items():
            threshold_map[str(k)] = float(v)

    case_reports = []
    pass_count = 0
    fail_count = 0
    for idx, item in enumerate(cases_raw):
        if not isinstance(item, Mapping):
            raise ValueError(f"cases[{idx}] must be object")
        report = _evaluate_single_case(item, threshold_map, idx=idx)
        case_reports.append(report)
        if bool(report["pass"]):
            pass_count += 1
        else:
            fail_count += 1

    summary = {
        "version": 1,
        "case_count": int(len(case_reports)),
        "pass_count": int(pass_count),
        "fail_count": int(fail_count),
        "pass_rate": float(pass_count / max(len(case_reports), 1)),
        "pass": bool(fail_count == 0),
        "thresholds": threshold_map,
        "cases": case_reports,
    }
    return summary


def _evaluate_single_case(
    case_payload: Mapping[str, Any],
    thresholds: Mapping[str, float],
    idx: int,
) -> Dict[str, Any]:
    case_id = str(case_payload.get("case_id", f"case_{idx:03d}"))
    candidate_adc_npz = str(case_payload["candidate_adc_npz"])
    reference_view_npz = str(case_payload["reference_view_npz"])
    candidate_adc_key = str(case_payload.get("candidate_adc_key", "adc"))
    candidate_adc_order = str(case_payload.get("candidate_adc_order", "sctr")).strip().lower()
    reference_view_key = str(case_payload.get("reference_view_key", "view"))

    adc_raw, adc_meta = load_adc_from_npz(candidate_adc_npz, adc_key=candidate_adc_key)
    adc_sctr = reorder_adc_to_sctr(adc_raw, adc_order=candidate_adc_order)
    cand_view = to_radarsimpy_view(adc_sctr)

    with np.load(str(reference_view_npz), allow_pickle=False) as payload:
        if reference_view_key not in payload:
            raise KeyError(f"{reference_view_npz} missing key: {reference_view_key}")
        ref_view = np.asarray(payload[reference_view_key])

    _validate_complex_3d(ref_view, key_name="reference_view")
    _validate_complex_3d(cand_view, key_name="candidate_view")
    if ref_view.shape != cand_view.shape:
        raise ValueError(
            f"case {case_id}: shape mismatch {cand_view.shape} != {ref_view.shape}"
        )

    metrics = _compute_view_metrics(reference=ref_view, candidate=cand_view)
    failures = _apply_thresholds(metrics=metrics, thresholds=thresholds)
    case_report = {
        "case_id": case_id,
        "candidate_adc_npz": str(Path(candidate_adc_npz).expanduser().resolve()),
        "reference_view_npz": str(Path(reference_view_npz).expanduser().resolve()),
        "adc_shape_sctr": [int(x) for x in adc_sctr.shape],
        "view_shape": [int(x) for x in cand_view.shape],
        "candidate_adc_meta": adc_meta,
        "metrics": metrics,
        "pass": bool(len(failures) == 0),
        "failures": failures,
    }
    return case_report


def _compute_view_metrics(reference: np.ndarray, candidate: np.ndarray) -> Dict[str, float]:
    ref = np.asarray(reference, dtype=np.complex128)
    cand = np.asarray(candidate, dtype=np.complex128)

    eps = float(np.finfo(np.float64).tiny)
    diff = cand - ref
    ref_pow = np.abs(ref) ** 2
    cand_pow = np.abs(cand) ** 2

    view_nmse = float(np.mean(np.abs(diff) ** 2) / (np.mean(np.abs(ref) ** 2) + eps))
    power_nmse = float(np.mean((cand_pow - ref_pow) ** 2) / (np.mean(ref_pow**2) + eps))
    mean_abs_error = float(np.mean(np.abs(diff)))
    max_abs_error = float(np.max(np.abs(diff)))

    ref_flat = ref.reshape(-1)
    cand_flat = cand.reshape(-1)
    denom = float(np.linalg.norm(ref_flat) * np.linalg.norm(cand_flat) + eps)
    corr = np.vdot(ref_flat, cand_flat) / denom
    complex_corr_abs = float(np.abs(corr))

    return {
        "view_nmse": view_nmse,
        "power_nmse": power_nmse,
        "mean_abs_error": mean_abs_error,
        "max_abs_error": max_abs_error,
        "complex_corr_abs": complex_corr_abs,
    }


def _apply_thresholds(metrics: Mapping[str, float], thresholds: Mapping[str, float]) -> list:
    failures = []
    for key, limit in thresholds.items():
        if key.endswith("_max"):
            metric_key = key[: -len("_max")]
            value = float(metrics.get(metric_key, 0.0))
            if value > float(limit):
                failures.append(
                    {
                        "metric": metric_key,
                        "value": value,
                        "limit": float(limit),
                        "mode": "max",
                    }
                )
        elif key.endswith("_min"):
            metric_key = key[: -len("_min")]
            value = float(metrics.get(metric_key, 0.0))
            if value < float(limit):
                failures.append(
                    {
                        "metric": metric_key,
                        "value": value,
                        "limit": float(limit),
                        "mode": "min",
                    }
                )
    return failures


def _validate_complex_3d(value: Any, key_name: str) -> None:
    arr = np.asarray(value)
    if arr.ndim != 3:
        raise ValueError(f"{key_name} must be 3D [channel,pulse,sample]")
    if not np.all(np.isfinite(np.real(arr))) or not np.all(np.isfinite(np.imag(arr))):
        raise ValueError(f"{key_name} contains non-finite values")
