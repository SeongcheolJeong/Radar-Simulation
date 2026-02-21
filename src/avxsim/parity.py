import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

import numpy as np


DEFAULT_PARITY_THRESHOLDS: Dict[str, float] = {
    "rd_peak_doppler_bin_abs_error_max": 1.0,
    "rd_peak_range_bin_abs_error_max": 1.0,
    "rd_peak_power_db_abs_error_max": 3.0,
    "rd_centroid_doppler_bin_abs_error_max": 1.5,
    "rd_centroid_range_bin_abs_error_max": 1.5,
    "rd_spread_doppler_rel_error_max": 0.35,
    "rd_spread_range_rel_error_max": 0.35,
    "rd_shape_nmse_max": 0.25,
    "ra_peak_angle_bin_abs_error_max": 1.0,
    "ra_peak_range_bin_abs_error_max": 1.0,
    "ra_peak_power_db_abs_error_max": 3.0,
    "ra_centroid_angle_bin_abs_error_max": 1.5,
    "ra_centroid_range_bin_abs_error_max": 1.5,
    "ra_spread_angle_rel_error_max": 0.35,
    "ra_spread_range_rel_error_max": 0.35,
    "ra_shape_nmse_max": 0.25,
}


@dataclass(frozen=True)
class PowerMapDescriptor:
    peak_axis0_bin: int
    peak_axis1_bin: int
    peak_power_db: float
    centroid_axis0_bin: float
    centroid_axis1_bin: float
    spread_axis0_bin: float
    spread_axis1_bin: float


def load_hybrid_estimation_npz(npz_path: str) -> Dict[str, Any]:
    p = Path(npz_path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    with np.load(str(p), allow_pickle=False) as payload:
        out: Dict[str, Any] = {}
        for key in payload.files:
            if key == "metadata_json":
                try:
                    out[key] = json.loads(str(payload[key].tolist()))
                except Exception:
                    out[key] = str(payload[key])
            else:
                out[key] = payload[key]
    return out


def compare_hybrid_estimation_npz(
    reference_npz: str,
    candidate_npz: str,
    thresholds: Mapping[str, float] = None,
) -> Dict[str, Any]:
    reference = load_hybrid_estimation_npz(reference_npz)
    candidate = load_hybrid_estimation_npz(candidate_npz)
    return compare_hybrid_estimation_payloads(
        reference=reference,
        candidate=candidate,
        thresholds=thresholds,
    )


def compare_hybrid_estimation_payloads(
    reference: Mapping[str, Any],
    candidate: Mapping[str, Any],
    thresholds: Mapping[str, float] = None,
) -> Dict[str, Any]:
    rd_ref_key = _pick_rd_key(reference)
    rd_cand_key = _pick_rd_key(candidate)
    rd_ref = _to_power_map(reference[rd_ref_key], key=rd_ref_key)
    rd_cand = _to_power_map(candidate[rd_cand_key], key=rd_cand_key)

    if "fx_ang" not in reference:
        raise KeyError("reference missing required key: fx_ang")
    if "fx_ang" not in candidate:
        raise KeyError("candidate missing required key: fx_ang")
    ra_ref = _to_power_map(reference["fx_ang"], key="fx_ang")
    ra_cand = _to_power_map(candidate["fx_ang"], key="fx_ang")

    _check_same_shape(rd_ref, rd_cand, "RD")
    _check_same_shape(ra_ref, ra_cand, "RA")

    metrics: Dict[str, float] = {}
    metrics.update(
        _compare_power_maps(
            reference=rd_ref,
            candidate=rd_cand,
            prefix="rd",
            axis0_name="doppler",
            axis1_name="range",
        )
    )
    metrics.update(
        _compare_power_maps(
            reference=ra_ref,
            candidate=ra_cand,
            prefix="ra",
            axis0_name="angle",
            axis1_name="range",
        )
    )

    threshold_map = dict(DEFAULT_PARITY_THRESHOLDS)
    if thresholds is not None:
        for key, value in thresholds.items():
            threshold_map[str(key)] = float(value)

    failures = []
    for t_key, max_value in threshold_map.items():
        if not t_key.endswith("_max"):
            continue
        metric_key = t_key[: -len("_max")]
        if metric_key not in metrics:
            continue
        value = float(metrics[metric_key])
        if value > float(max_value):
            failures.append(
                {
                    "metric": metric_key,
                    "value": value,
                    "limit": float(max_value),
                }
            )

    return {
        "pass": len(failures) == 0,
        "metrics": metrics,
        "thresholds": threshold_map,
        "failures": failures,
        "rd_reference_key": rd_ref_key,
        "rd_candidate_key": rd_cand_key,
        "rd_shape": list(rd_ref.shape),
        "ra_shape": list(ra_ref.shape),
    }


def _pick_rd_key(payload: Mapping[str, Any]) -> str:
    if "fx_dop_win" in payload:
        return "fx_dop_win"
    if "fx_dop" in payload:
        return "fx_dop"
    raise KeyError("missing required key: fx_dop_win or fx_dop")


def _to_power_map(arr: Any, key: str) -> np.ndarray:
    x = np.asarray(arr)
    if x.ndim != 2:
        raise ValueError(f"{key} must be 2D")
    if np.iscomplexobj(x):
        x = np.abs(x) ** 2
    x = np.real(np.asarray(x, dtype=np.float64))
    x = np.maximum(x, np.finfo(np.float64).tiny)
    if not np.all(np.isfinite(x)):
        raise ValueError(f"{key} contains non-finite values")
    return x


def _check_same_shape(a: np.ndarray, b: np.ndarray, label: str) -> None:
    if a.shape != b.shape:
        raise ValueError(f"{label} shape mismatch: {a.shape} vs {b.shape}")


def _compare_power_maps(
    reference: np.ndarray,
    candidate: np.ndarray,
    prefix: str,
    axis0_name: str,
    axis1_name: str,
) -> Dict[str, float]:
    ref = _describe_power_map(reference)
    cand = _describe_power_map(candidate)
    out = {
        f"{prefix}_peak_{axis0_name}_bin_abs_error": abs(
            float(cand.peak_axis0_bin) - float(ref.peak_axis0_bin)
        ),
        f"{prefix}_peak_{axis1_name}_bin_abs_error": abs(
            float(cand.peak_axis1_bin) - float(ref.peak_axis1_bin)
        ),
        f"{prefix}_peak_power_db_abs_error": abs(float(cand.peak_power_db) - float(ref.peak_power_db)),
        f"{prefix}_centroid_{axis0_name}_bin_abs_error": abs(
            float(cand.centroid_axis0_bin) - float(ref.centroid_axis0_bin)
        ),
        f"{prefix}_centroid_{axis1_name}_bin_abs_error": abs(
            float(cand.centroid_axis1_bin) - float(ref.centroid_axis1_bin)
        ),
        f"{prefix}_spread_{axis0_name}_rel_error": _relative_error(
            cand.spread_axis0_bin, ref.spread_axis0_bin
        ),
        f"{prefix}_spread_{axis1_name}_rel_error": _relative_error(
            cand.spread_axis1_bin, ref.spread_axis1_bin
        ),
        f"{prefix}_shape_nmse": _shape_nmse(reference, candidate),
    }
    return out


def _describe_power_map(power_map: np.ndarray) -> PowerMapDescriptor:
    p = np.asarray(power_map, dtype=np.float64)
    if p.ndim != 2:
        raise ValueError("power_map must be 2D")

    peak_idx = np.unravel_index(int(np.argmax(p)), p.shape)
    peak0, peak1 = int(peak_idx[0]), int(peak_idx[1])
    peak_power_db = 10.0 * np.log10(float(p[peak0, peak1]))

    total = float(np.sum(p))
    axis0 = np.arange(p.shape[0], dtype=np.float64)
    axis1 = np.arange(p.shape[1], dtype=np.float64)
    marg0 = np.sum(p, axis=1)
    marg1 = np.sum(p, axis=0)

    c0 = float(np.sum(axis0 * marg0) / total)
    c1 = float(np.sum(axis1 * marg1) / total)
    s0 = float(np.sqrt(np.sum(((axis0 - c0) ** 2) * marg0) / total))
    s1 = float(np.sqrt(np.sum(((axis1 - c1) ** 2) * marg1) / total))

    return PowerMapDescriptor(
        peak_axis0_bin=peak0,
        peak_axis1_bin=peak1,
        peak_power_db=peak_power_db,
        centroid_axis0_bin=c0,
        centroid_axis1_bin=c1,
        spread_axis0_bin=s0,
        spread_axis1_bin=s1,
    )


def _relative_error(value: float, reference: float) -> float:
    eps = 1e-12
    return abs(float(value) - float(reference)) / (abs(float(reference)) + eps)


def _shape_nmse(reference: np.ndarray, candidate: np.ndarray) -> float:
    eps = 1e-12
    ref = np.asarray(reference, dtype=np.float64)
    cand = np.asarray(candidate, dtype=np.float64)
    ref_n = ref / (np.sum(ref) + eps)
    cand_n = cand / (np.sum(cand) + eps)
    diff = cand_n - ref_n
    return float(np.mean(diff**2) / (np.mean(ref_n**2) + eps))

