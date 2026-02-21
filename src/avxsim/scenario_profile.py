import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np

from .calibration import parse_jones_matrix
from .parity import DEFAULT_PARITY_THRESHOLDS


def derive_parity_thresholds(
    metric_reports: Sequence[Mapping[str, float]],
    quantile: float = 0.95,
    margin: float = 1.25,
    floor_thresholds: Optional[Mapping[str, float]] = DEFAULT_PARITY_THRESHOLDS,
) -> Dict[str, float]:
    if not (0.0 < float(quantile) <= 1.0):
        raise ValueError("quantile must be in (0, 1]")
    if float(margin) <= 0.0:
        raise ValueError("margin must be positive")

    values_by_metric: Dict[str, list] = {}
    for report in metric_reports:
        for key, value in report.items():
            values_by_metric.setdefault(str(key), []).append(float(value))

    out: Dict[str, float] = {}
    for metric, values in values_by_metric.items():
        arr = np.asarray(values, dtype=np.float64)
        if arr.size == 0:
            continue
        qv = float(np.quantile(arr, float(quantile)))
        out[f"{metric}_max"] = float(max(0.0, qv) * float(margin))

    if floor_thresholds is not None:
        for key, value in floor_thresholds.items():
            out[str(key)] = max(float(value), float(out.get(str(key), 0.0)))
    return out


def build_scenario_profile_payload(
    scenario_id: str,
    global_jones_matrix: np.ndarray,
    parity_thresholds: Mapping[str, float],
    reference_estimation_npz: Optional[str] = None,
    fit_metrics: Optional[Mapping[str, Any]] = None,
    train_estimation_npz: Optional[Sequence[str]] = None,
    threshold_derivation: Optional[Mapping[str, Any]] = None,
    motion_compensation_defaults: Optional[Mapping[str, Any]] = None,
    motion_tuning_summary: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    sid = str(scenario_id).strip()
    if sid == "":
        raise ValueError("scenario_id must be non-empty")
    j = parse_jones_matrix(global_jones_matrix)
    payload: Dict[str, Any] = {
        "version": 1,
        "scenario_id": sid,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "global_jones_matrix": _encode_matrix(j),
        "parity_thresholds": {str(k): float(v) for k, v in parity_thresholds.items()},
    }
    if reference_estimation_npz is not None:
        payload["reference_estimation_npz"] = str(reference_estimation_npz)
    if fit_metrics is not None:
        payload["fit_metrics"] = _to_jsonable(fit_metrics)
    if train_estimation_npz is not None:
        payload["train_estimation_npz"] = [str(x) for x in train_estimation_npz]
    if threshold_derivation is not None:
        payload["threshold_derivation"] = _to_jsonable(threshold_derivation)
    if motion_compensation_defaults is not None:
        payload["motion_compensation_defaults"] = _normalize_motion_defaults(
            motion_compensation_defaults
        )
    if motion_tuning_summary is not None:
        payload["motion_tuning_summary"] = _to_jsonable(motion_tuning_summary)
    return payload


def save_scenario_profile_json(out_json: str, payload: Mapping[str, Any]) -> None:
    Path(out_json).write_text(json.dumps(_to_jsonable(payload), indent=2), encoding="utf-8")


def load_scenario_profile_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("scenario profile must be a JSON object")
    if "global_jones_matrix" not in payload:
        raise ValueError("scenario profile missing global_jones_matrix")
    if "parity_thresholds" not in payload:
        raise ValueError("scenario profile missing parity_thresholds")
    out = dict(payload)
    out["global_jones_matrix_array"] = parse_jones_matrix(payload["global_jones_matrix"])
    if not isinstance(out["parity_thresholds"], dict):
        raise ValueError("parity_thresholds must be an object")
    out["parity_thresholds"] = {
        str(k): float(v) for k, v in out["parity_thresholds"].items()
    }
    if "motion_compensation_defaults" in out:
        out["motion_compensation_defaults"] = _normalize_motion_defaults(
            out["motion_compensation_defaults"]
        )
    else:
        out["motion_compensation_defaults"] = {
            "enabled": False,
            "fd_hz": None,
            "chirp_interval_s": None,
            "reference_tx": None,
        }
    return out


def _normalize_motion_defaults(value: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("motion_compensation_defaults must be object")
    return {
        "enabled": bool(value.get("enabled", False)),
        "fd_hz": None if value.get("fd_hz", None) is None else float(value["fd_hz"]),
        "chirp_interval_s": None
        if value.get("chirp_interval_s", None) is None
        else float(value["chirp_interval_s"]),
        "reference_tx": None
        if value.get("reference_tx", None) is None
        else int(value["reference_tx"]),
    }


def _encode_matrix(matrix: np.ndarray):
    j = np.asarray(matrix, dtype=np.complex128).reshape(2, 2)
    flat = j.reshape(-1)
    return [{"re": float(np.real(v)), "im": float(np.imag(v))} for v in flat]


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, (np.complexfloating, complex)):
        return {"re": float(np.real(value)), "im": float(np.imag(value))}
    return value
