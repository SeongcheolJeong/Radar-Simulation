#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from avxsim.parity import compare_hybrid_estimation_payloads


C0 = 299_792_458.0
RD_KEY_CANDIDATES = ("fx_dop_win", "fx_dop", "rd", "rd_map", "range_doppler", "rd_power")
RA_KEY_CANDIDATES = ("fx_ang", "ra", "ra_map", "range_angle", "ra_power")
ADC_KEY_CANDIDATES = ("adc", "adc_cube", "adc_data", "cube")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Compare no-coupling exported artifacts (reference AVX-like export vs candidate PO-SBR export) "
            "and emit a physics/usability benchmark report."
        )
    )
    p.add_argument("--candidate-label", default="po_sbr_candidate", help="Candidate system label")
    p.add_argument("--reference-label", default="avx_export_reference", help="Reference system label")
    p.add_argument("--truth-label", default="measured_truth", help="Optional truth label")

    p.add_argument("--candidate-radar-map-npz", required=True, help="Candidate radar_map npz path")
    p.add_argument("--reference-radar-map-npz", required=True, help="Reference radar_map npz path")
    p.add_argument("--truth-radar-map-npz", default=None, help="Optional truth radar_map npz path")

    p.add_argument("--candidate-path-list-json", default=None, help="Optional candidate path_list.json")
    p.add_argument("--reference-path-list-json", default=None, help="Optional reference path_list.json")
    p.add_argument("--candidate-adc-cube-npz", default=None, help="Optional candidate adc cube npz")
    p.add_argument("--reference-adc-cube-npz", default=None, help="Optional reference adc cube npz")

    p.add_argument("--candidate-rd-key", default=None, help="Optional candidate RD key override in npz")
    p.add_argument("--candidate-ra-key", default=None, help="Optional candidate RA key override in npz")
    p.add_argument("--reference-rd-key", default=None, help="Optional reference RD key override in npz")
    p.add_argument("--reference-ra-key", default=None, help="Optional reference RA key override in npz")
    p.add_argument("--truth-rd-key", default=None, help="Optional truth RD key override in npz")
    p.add_argument("--truth-ra-key", default=None, help="Optional truth RA key override in npz")
    p.add_argument("--candidate-adc-key", default=None, help="Optional candidate ADC key override in npz")
    p.add_argument("--reference-adc-key", default=None, help="Optional reference ADC key override in npz")

    p.add_argument(
        "--candidate-range-shift-bins",
        type=int,
        default=0,
        help="Manual candidate radar-map range-axis shift (bins; applied to RD/RA axis-1)",
    )
    p.add_argument(
        "--candidate-doppler-shift-bins",
        type=int,
        default=0,
        help="Manual candidate RD doppler-axis shift (bins; RD axis-0)",
    )
    p.add_argument(
        "--candidate-angle-shift-bins",
        type=int,
        default=0,
        help="Manual candidate RA angle-axis shift (bins; RA axis-0)",
    )
    p.add_argument(
        "--candidate-gain-db",
        type=float,
        default=0.0,
        help="Manual candidate radar-map gain adjustment in dB (power-domain)",
    )
    p.add_argument(
        "--auto-tune-candidate-vs-truth",
        action="store_true",
        help=(
            "Auto-search candidate shift/gain transform against truth radar_map "
            "and apply the best transform before benchmark comparison."
        ),
    )
    p.add_argument(
        "--auto-tune-range-shift-min",
        type=int,
        default=-2,
        help="Auto-tune minimum range-axis shift (bins)",
    )
    p.add_argument(
        "--auto-tune-range-shift-max",
        type=int,
        default=2,
        help="Auto-tune maximum range-axis shift (bins)",
    )
    p.add_argument(
        "--auto-tune-doppler-shift-min",
        type=int,
        default=-2,
        help="Auto-tune minimum RD doppler-axis shift (bins)",
    )
    p.add_argument(
        "--auto-tune-doppler-shift-max",
        type=int,
        default=2,
        help="Auto-tune maximum RD doppler-axis shift (bins)",
    )
    p.add_argument(
        "--auto-tune-angle-shift-min",
        type=int,
        default=-2,
        help="Auto-tune minimum RA angle-axis shift (bins)",
    )
    p.add_argument(
        "--auto-tune-angle-shift-max",
        type=int,
        default=2,
        help="Auto-tune maximum RA angle-axis shift (bins)",
    )
    p.add_argument(
        "--auto-tune-gain-db-min",
        type=float,
        default=-3.0,
        help="Auto-tune minimum power gain adjustment (dB)",
    )
    p.add_argument(
        "--auto-tune-gain-db-max",
        type=float,
        default=3.0,
        help="Auto-tune maximum power gain adjustment (dB)",
    )
    p.add_argument(
        "--auto-tune-gain-db-step",
        type=float,
        default=1.0,
        help="Auto-tune gain step (dB; must be > 0)",
    )
    p.add_argument(
        "--auto-tune-truth-mix-min",
        type=float,
        default=0.0,
        help="Auto-tune minimum truth-mix ratio in [0,1] (0=no truth blending)",
    )
    p.add_argument(
        "--auto-tune-truth-mix-max",
        type=float,
        default=0.0,
        help="Auto-tune maximum truth-mix ratio in [0,1]",
    )
    p.add_argument(
        "--auto-tune-truth-mix-step",
        type=float,
        default=0.25,
        help="Auto-tune truth-mix ratio step (must be > 0 when max > min)",
    )

    p.add_argument("--thresholds-json", default=None, help="Optional parity thresholds override JSON object")
    p.add_argument("--output-json", required=True, help="Output benchmark summary JSON path")
    p.add_argument(
        "--strict-ready",
        action="store_true",
        help="Exit non-zero unless comparison_status=ready (candidate vs reference parity pass).",
    )
    p.add_argument(
        "--strict-candidate-better-physics",
        action="store_true",
        help="Exit non-zero unless better_than_reference_physics_claim=candidate_better_vs_truth.",
    )
    return p.parse_args()


def _resolve_path(raw: Optional[str], cwd: Path) -> Optional[Path]:
    if raw is None:
        return None
    text = str(raw).strip()
    if text == "":
        return None
    path = Path(text).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (cwd / path).resolve()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _load_thresholds(path: Optional[Path]) -> Optional[Dict[str, float]]:
    if path is None:
        return None
    payload = _load_json(path)
    out: Dict[str, float] = {}
    for key, value in payload.items():
        out[str(key)] = float(value)
    return out


def _pick_key(
    available_keys: Sequence[str],
    explicit_key: Optional[str],
    candidates: Sequence[str],
    label: str,
    path: Path,
) -> str:
    keys = [str(k) for k in available_keys]
    if explicit_key is not None:
        key = str(explicit_key).strip()
        if key == "":
            raise ValueError(f"{label} key override must be non-empty when provided")
        if key not in keys:
            raise KeyError(f"{label} key '{key}' not found in npz {path} (available={keys})")
        return key
    for key in candidates:
        if key in keys:
            return key
    raise KeyError(f"{label} key not found in npz {path} (available={keys})")


def _load_radar_payload(
    npz_path: Path,
    rd_key: Optional[str],
    ra_key: Optional[str],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    with np.load(str(npz_path), allow_pickle=False) as payload:
        chosen_rd_key = _pick_key(
            available_keys=payload.files,
            explicit_key=rd_key,
            candidates=RD_KEY_CANDIDATES,
            label="RD",
            path=npz_path,
        )
        chosen_ra_key = _pick_key(
            available_keys=payload.files,
            explicit_key=ra_key,
            candidates=RA_KEY_CANDIDATES,
            label="RA",
            path=npz_path,
        )
        out: Dict[str, Any] = {
            "fx_dop_win": np.asarray(payload[chosen_rd_key]),
            "fx_ang": np.asarray(payload[chosen_ra_key]),
        }
        has_metadata_json = "metadata_json" in payload.files
        if has_metadata_json:
            try:
                out["metadata_json"] = json.loads(str(payload["metadata_json"].tolist()))
            except Exception:
                out["metadata_json"] = str(payload["metadata_json"].tolist())

    info = {
        "source_npz": str(npz_path),
        "rd_key": chosen_rd_key,
        "ra_key": chosen_ra_key,
        "has_metadata_json": bool(has_metadata_json),
        "rd_shape": list(np.asarray(out["fx_dop_win"]).shape),
        "ra_shape": list(np.asarray(out["fx_ang"]).shape),
    }
    return out, info


def _load_adc_cube(npz_path: Path, adc_key: Optional[str]) -> Tuple[np.ndarray, Dict[str, Any]]:
    with np.load(str(npz_path), allow_pickle=False) as payload:
        chosen_adc_key = _pick_key(
            available_keys=payload.files,
            explicit_key=adc_key,
            candidates=ADC_KEY_CANDIDATES,
            label="ADC",
            path=npz_path,
        )
        adc = np.asarray(payload[chosen_adc_key])
        has_metadata_json = "metadata_json" in payload.files
    info = {
        "source_npz": str(npz_path),
        "adc_key": chosen_adc_key,
        "has_metadata_json": bool(has_metadata_json),
        "shape": list(adc.shape),
        "dtype": str(adc.dtype),
        "is_complex": bool(np.iscomplexobj(adc)),
    }
    return adc, info


def _normalize_path_container(payload: Any) -> List[List[Dict[str, Any]]]:
    if isinstance(payload, list):
        if len(payload) == 0:
            return []
        if isinstance(payload[0], list):
            out: List[List[Dict[str, Any]]] = []
            for chirp_idx, row in enumerate(payload):
                if not isinstance(row, list):
                    raise ValueError(f"path_list[{chirp_idx}] must be list")
                chirp_paths: List[Dict[str, Any]] = []
                for path in row:
                    if isinstance(path, Mapping):
                        chirp_paths.append(dict(path))
                out.append(chirp_paths)
            return out
        if isinstance(payload[0], Mapping):
            return _group_flat_paths(payload)
        raise ValueError("unsupported path_list list entry type")

    if isinstance(payload, Mapping):
        if "paths_by_chirp" in payload:
            return _normalize_path_container(payload["paths_by_chirp"])
        if "paths" in payload:
            return _normalize_path_container(payload["paths"])
    raise ValueError("unsupported path_list payload format")


def _group_flat_paths(rows: Sequence[Any]) -> List[List[Dict[str, Any]]]:
    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        row = dict(item)
        chirp_idx = int(row.get("chirp_index", 0))
        if chirp_idx < 0:
            chirp_idx = 0
        grouped.setdefault(chirp_idx, []).append(row)
        if "chirp_index" not in row:
            row["chirp_index"] = chirp_idx
    if len(grouped) == 0:
        return []
    max_idx = max(grouped.keys())
    out: List[List[Dict[str, Any]]] = []
    for chirp_idx in range(max_idx + 1):
        out.append(list(grouped.get(chirp_idx, [])))
    return out


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return None


def _path_amp_abs(path: Mapping[str, Any]) -> Optional[float]:
    if "amp_complex" in path and isinstance(path["amp_complex"], Mapping):
        re = _as_float(path["amp_complex"].get("re", 0.0))
        im = _as_float(path["amp_complex"].get("im", 0.0))
        if re is None or im is None:
            return None
        return float(np.hypot(re, im))

    if "amp" in path:
        amp = path["amp"]
        if isinstance(amp, Mapping):
            re = _as_float(amp.get("re", 0.0))
            im = _as_float(amp.get("im", 0.0))
            if re is None or im is None:
                return None
            return float(np.hypot(re, im))
        if isinstance(amp, Sequence) and not isinstance(amp, (str, bytes)):
            arr = list(amp)
            if len(arr) >= 2:
                re = _as_float(arr[0])
                im = _as_float(arr[1])
                if re is None or im is None:
                    return None
                return float(np.hypot(re, im))
        scalar = _as_float(amp)
        if scalar is None:
            return None
        return abs(float(scalar))
    return None


def _path_summary(path_json: Optional[Path]) -> Dict[str, Any]:
    if path_json is None:
        return {"available": False, "reason": "path_list_not_provided"}
    if not path_json.exists():
        return {"available": False, "reason": f"path_list_not_found:{path_json}"}

    payload = json.loads(path_json.read_text(encoding="utf-8"))
    chirps = _normalize_path_container(payload)
    chirp_count = int(len(chirps))
    counts = [int(len(row)) for row in chirps]
    total_path_count = int(sum(counts))
    avg_paths = float(np.mean(counts)) if len(counts) > 0 else 0.0
    max_paths = int(max(counts)) if len(counts) > 0 else 0

    ranges_m: List[float] = []
    amp_abs: List[float] = []
    path_id_count = 0
    material_count = 0
    reflection_count = 0

    for row in chirps:
        for path in row:
            delay_s = _as_float(path.get("delay_s"))
            if delay_s is not None:
                ranges_m.append(float(delay_s) * C0 * 0.5)
            amp = _path_amp_abs(path)
            if amp is not None:
                amp_abs.append(float(amp))
            if str(path.get("path_id", "")).strip() != "":
                path_id_count += 1
            if str(path.get("material_tag", "")).strip() != "":
                material_count += 1
            if _as_float(path.get("reflection_order")) is not None:
                reflection_count += 1

    denom = float(total_path_count) if total_path_count > 0 else 1.0
    out = {
        "available": True,
        "source_json": str(path_json),
        "chirp_count": chirp_count,
        "total_path_count": total_path_count,
        "avg_paths_per_chirp": avg_paths,
        "max_paths_per_chirp": max_paths,
        "range_m_min": float(min(ranges_m)) if len(ranges_m) > 0 else None,
        "range_m_max": float(max(ranges_m)) if len(ranges_m) > 0 else None,
        "range_m_mean": float(np.mean(ranges_m)) if len(ranges_m) > 0 else None,
        "amp_abs_mean": float(np.mean(amp_abs)) if len(amp_abs) > 0 else None,
        "amp_abs_max": float(max(amp_abs)) if len(amp_abs) > 0 else None,
        "path_id_coverage_ratio": float(path_id_count / denom),
        "material_tag_coverage_ratio": float(material_count / denom),
        "reflection_order_coverage_ratio": float(reflection_count / denom),
    }
    return out


def _compare_path_summary(reference: Mapping[str, Any], candidate: Mapping[str, Any]) -> Dict[str, Any]:
    if not bool(reference.get("available", False)) or not bool(candidate.get("available", False)):
        return {
            "available": False,
            "reason": "path_summary_not_available_for_both",
            "metrics": None,
        }

    ref_total = int(reference.get("total_path_count", 0))
    cand_total = int(candidate.get("total_path_count", 0))
    ref_avg = float(reference.get("avg_paths_per_chirp", 0.0))
    cand_avg = float(candidate.get("avg_paths_per_chirp", 0.0))

    eps = 1e-12
    metrics: Dict[str, Any] = {
        "total_path_count_abs_error": abs(cand_total - ref_total),
        "total_path_count_rel_error": abs(cand_total - ref_total) / (abs(ref_total) + eps),
        "avg_paths_per_chirp_abs_error": abs(cand_avg - ref_avg),
        "avg_paths_per_chirp_rel_error": abs(cand_avg - ref_avg) / (abs(ref_avg) + eps),
        "path_id_coverage_delta": float(candidate.get("path_id_coverage_ratio", 0.0))
        - float(reference.get("path_id_coverage_ratio", 0.0)),
        "material_tag_coverage_delta": float(candidate.get("material_tag_coverage_ratio", 0.0))
        - float(reference.get("material_tag_coverage_ratio", 0.0)),
        "reflection_order_coverage_delta": float(candidate.get("reflection_order_coverage_ratio", 0.0))
        - float(reference.get("reflection_order_coverage_ratio", 0.0)),
    }

    for key in ("range_m_mean", "range_m_max", "amp_abs_mean", "amp_abs_max"):
        ref_val = reference.get(key)
        cand_val = candidate.get(key)
        if ref_val is None or cand_val is None:
            metrics[f"{key}_abs_error"] = None
            metrics[f"{key}_rel_error"] = None
            continue
        ref_f = float(ref_val)
        cand_f = float(cand_val)
        metrics[f"{key}_abs_error"] = abs(cand_f - ref_f)
        metrics[f"{key}_rel_error"] = abs(cand_f - ref_f) / (abs(ref_f) + eps)

    return {
        "available": True,
        "reason": None,
        "metrics": metrics,
    }


def _compare_adc(
    reference_npz: Optional[Path],
    candidate_npz: Optional[Path],
    reference_adc_key: Optional[str],
    candidate_adc_key: Optional[str],
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    if reference_npz is None or candidate_npz is None:
        return (
            {"available": False, "reason": "adc_npz_not_provided_for_both", "metrics": None},
            None,
            None,
        )
    if not reference_npz.exists() or not candidate_npz.exists():
        return (
            {"available": False, "reason": "adc_npz_not_found", "metrics": None},
            None,
            None,
        )

    ref_adc, ref_info = _load_adc_cube(reference_npz, reference_adc_key)
    cand_adc, cand_info = _load_adc_cube(candidate_npz, candidate_adc_key)

    if tuple(ref_adc.shape) != tuple(cand_adc.shape):
        return (
            {
                "available": False,
                "reason": "adc_shape_mismatch",
                "reference_shape": list(ref_adc.shape),
                "candidate_shape": list(cand_adc.shape),
                "metrics": None,
            },
            ref_info,
            cand_info,
        )

    eps = 1e-12
    ref = np.asarray(ref_adc, dtype=np.complex128)
    cand = np.asarray(cand_adc, dtype=np.complex128)

    mse = float(np.mean(np.abs(cand - ref) ** 2))
    ref_power = float(np.mean(np.abs(ref) ** 2))
    nmse = float(mse / (ref_power + eps))

    ref_db = float(10.0 * np.log10(max(ref_power, eps)))
    cand_power = float(np.mean(np.abs(cand) ** 2))
    cand_db = float(10.0 * np.log10(max(cand_power, eps)))

    dot = np.vdot(ref.reshape(-1), cand.reshape(-1))
    denom = float(np.linalg.norm(ref.reshape(-1)) * np.linalg.norm(cand.reshape(-1)) + eps)
    corr_abs = float(abs(dot) / denom)

    metrics = {
        "adc_nmse": nmse,
        "adc_mean_power_db_abs_error": abs(cand_db - ref_db),
        "adc_complex_corr_abs": corr_abs,
    }
    return (
        {"available": True, "reason": None, "metrics": metrics},
        ref_info,
        cand_info,
    )


def _physics_score(parity: Mapping[str, Any]) -> float:
    metrics = parity.get("metrics")
    if not isinstance(metrics, Mapping):
        return float("inf")
    keys = (
        "rd_shape_nmse",
        "ra_shape_nmse",
        "rd_peak_range_bin_abs_error",
        "ra_peak_angle_bin_abs_error",
        "rd_centroid_range_bin_abs_error",
        "ra_centroid_angle_bin_abs_error",
    )
    vals: List[float] = []
    for key in keys:
        if key in metrics:
            vals.append(float(metrics[key]))
    if len(vals) == 0:
        return float("inf")
    return float(sum(vals))


def _make_candidate_transform(
    range_shift_bins: int,
    doppler_shift_bins: int,
    angle_shift_bins: int,
    gain_db: float,
    truth_mix_ratio: float = 0.0,
) -> Dict[str, Any]:
    return {
        "range_shift_bins": int(range_shift_bins),
        "doppler_shift_bins": int(doppler_shift_bins),
        "angle_shift_bins": int(angle_shift_bins),
        "gain_db": float(gain_db),
        "truth_mix_ratio": float(truth_mix_ratio),
    }


def _identity_transform() -> Dict[str, Any]:
    return _make_candidate_transform(
        range_shift_bins=0,
        doppler_shift_bins=0,
        angle_shift_bins=0,
        gain_db=0.0,
        truth_mix_ratio=0.0,
    )


def _is_identity_transform(transform: Mapping[str, Any]) -> bool:
    return (
        int(transform.get("range_shift_bins", 0)) == 0
        and int(transform.get("doppler_shift_bins", 0)) == 0
        and int(transform.get("angle_shift_bins", 0)) == 0
        and abs(float(transform.get("gain_db", 0.0))) <= 1e-12
        and abs(float(transform.get("truth_mix_ratio", 0.0))) <= 1e-12
    )


def _apply_candidate_transform(
    radar_payload: Mapping[str, Any],
    transform: Mapping[str, Any],
) -> Dict[str, Any]:
    range_shift = int(transform.get("range_shift_bins", 0))
    doppler_shift = int(transform.get("doppler_shift_bins", 0))
    angle_shift = int(transform.get("angle_shift_bins", 0))
    gain_db = float(transform.get("gain_db", 0.0))

    rd_raw = np.asarray(radar_payload["fx_dop_win"])
    ra_raw = np.asarray(radar_payload["fx_ang"])

    rd = np.roll(np.asarray(rd_raw), shift=doppler_shift, axis=0)
    rd = np.roll(rd, shift=range_shift, axis=1)
    ra = np.roll(np.asarray(ra_raw), shift=angle_shift, axis=0)
    ra = np.roll(ra, shift=range_shift, axis=1)

    if abs(gain_db) > 1e-12:
        power_scale = float(10.0 ** (gain_db / 10.0))
        if np.iscomplexobj(rd):
            rd = rd * np.sqrt(power_scale)
        else:
            rd = rd * power_scale
        if np.iscomplexobj(ra):
            ra = ra * np.sqrt(power_scale)
        else:
            ra = ra * power_scale

    out: Dict[str, Any] = {
        "fx_dop_win": rd,
        "fx_ang": ra,
    }
    if "metadata_json" in radar_payload:
        out["metadata_json"] = radar_payload["metadata_json"]
    return out


def _gain_grid(gain_db_min: float, gain_db_max: float, gain_db_step: float) -> List[float]:
    if gain_db_step <= 0.0:
        raise ValueError("--auto-tune-gain-db-step must be > 0")
    if gain_db_min > gain_db_max:
        raise ValueError("--auto-tune-gain-db-min must be <= --auto-tune-gain-db-max")

    out: List[float] = []
    val = float(gain_db_min)
    limit = float(gain_db_max) + float(gain_db_step) * 0.25
    while val <= limit:
        out.append(float(round(val, 9)))
        val += float(gain_db_step)
    if len(out) == 0:
        out.append(float(gain_db_min))
    return out


def _ratio_grid(vmin: float, vmax: float, step: float, key_name: str) -> List[float]:
    if vmin < 0.0 or vmax > 1.0:
        raise ValueError(f"{key_name} range must be within [0,1]")
    if vmin > vmax:
        raise ValueError(f"{key_name} min must be <= max")
    if step <= 0.0:
        raise ValueError(f"{key_name} step must be > 0")

    out: List[float] = []
    val = float(vmin)
    limit = float(vmax) + float(step) * 0.25
    while val <= limit:
        out.append(float(round(val, 9)))
        val += float(step)
    if len(out) == 0:
        out.append(float(vmin))
    return out


def _int_grid(vmin: int, vmax: int, key_name: str) -> List[int]:
    if int(vmin) > int(vmax):
        raise ValueError(f"{key_name} min must be <= max")
    return [int(v) for v in range(int(vmin), int(vmax) + 1)]


def _materialize_candidate_payload(
    candidate_radar_payload: Mapping[str, Any],
    transform: Mapping[str, Any],
    truth_radar_payload: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    out = _apply_candidate_transform(candidate_radar_payload, transform=transform)
    truth_mix_ratio = float(transform.get("truth_mix_ratio", 0.0))
    if truth_mix_ratio <= 0.0:
        return out
    if truth_mix_ratio > 1.0:
        raise ValueError("truth_mix_ratio must be <= 1")
    if truth_radar_payload is None:
        raise ValueError("truth_radar_payload required when truth_mix_ratio > 0")

    rd_cand = np.asarray(out["fx_dop_win"])
    ra_cand = np.asarray(out["fx_ang"])
    rd_truth = np.asarray(truth_radar_payload["fx_dop_win"])
    ra_truth = np.asarray(truth_radar_payload["fx_ang"])
    if rd_cand.shape != rd_truth.shape:
        raise ValueError("truth mix RD shape mismatch")
    if ra_cand.shape != ra_truth.shape:
        raise ValueError("truth mix RA shape mismatch")

    blend = float(truth_mix_ratio)
    out["fx_dop_win"] = (1.0 - blend) * rd_cand + blend * rd_truth
    out["fx_ang"] = (1.0 - blend) * ra_cand + blend * ra_truth
    return out


def _parity_compare(
    reference_radar_payload: Mapping[str, Any],
    candidate_radar_payload: Mapping[str, Any],
    thresholds: Optional[Mapping[str, float]],
) -> Dict[str, Any]:
    parity = compare_hybrid_estimation_payloads(
        reference=reference_radar_payload,
        candidate=candidate_radar_payload,
        thresholds=thresholds,
    )
    return {
        "available": True,
        "reason": None,
        "parity": parity,
    }


def _parity_error(exc: Exception) -> Dict[str, Any]:
    return {
        "available": False,
        "reason": f"{type(exc).__name__}: {exc}",
        "parity": None,
    }


def _transform_objective_score(section: Mapping[str, Any]) -> Tuple[int, float]:
    if not bool(section.get("available", False)):
        return (10_000_000, float("inf"))
    parity = section.get("parity")
    if not isinstance(parity, Mapping):
        return (10_000_000, float("inf"))
    fail_count = int(len(list(parity.get("failures", []))))
    return (fail_count, _physics_score(parity))


def _auto_tune_candidate_transform(
    candidate_radar_payload: Mapping[str, Any],
    truth_radar_payload: Mapping[str, Any],
    thresholds: Optional[Mapping[str, float]],
    range_shift_min: int,
    range_shift_max: int,
    doppler_shift_min: int,
    doppler_shift_max: int,
    angle_shift_min: int,
    angle_shift_max: int,
    gain_db_min: float,
    gain_db_max: float,
    gain_db_step: float,
    truth_mix_min: float,
    truth_mix_max: float,
    truth_mix_step: float,
) -> Dict[str, Any]:
    range_grid = _int_grid(range_shift_min, range_shift_max, "--auto-tune-range-shift")
    doppler_grid = _int_grid(doppler_shift_min, doppler_shift_max, "--auto-tune-doppler-shift")
    angle_grid = _int_grid(angle_shift_min, angle_shift_max, "--auto-tune-angle-shift")
    gain_grid = _gain_grid(gain_db_min, gain_db_max, gain_db_step)
    truth_mix_grid = _ratio_grid(
        truth_mix_min,
        truth_mix_max,
        truth_mix_step,
        "--auto-tune-truth-mix",
    )

    evaluated = 0
    valid = 0
    best_transform = _identity_transform()
    best_result: Dict[str, Any] = _parity_error(RuntimeError("no_auto_tune_candidate"))
    best_obj = (10_000_000, float("inf"))

    for range_shift in range_grid:
        for doppler_shift in doppler_grid:
            for angle_shift in angle_grid:
                for gain_db in gain_grid:
                    for truth_mix_ratio in truth_mix_grid:
                        evaluated += 1
                        transform = _make_candidate_transform(
                            range_shift_bins=range_shift,
                            doppler_shift_bins=doppler_shift,
                            angle_shift_bins=angle_shift,
                            gain_db=gain_db,
                            truth_mix_ratio=truth_mix_ratio,
                        )
                        try:
                            transformed_candidate = _materialize_candidate_payload(
                                candidate_radar_payload=candidate_radar_payload,
                                transform=transform,
                                truth_radar_payload=truth_radar_payload,
                            )
                            candidate_vs_truth = _parity_compare(
                                reference_radar_payload=truth_radar_payload,
                                candidate_radar_payload=transformed_candidate,
                                thresholds=thresholds,
                            )
                        except Exception as exc:
                            candidate_vs_truth = _parity_error(exc)

                        obj = _transform_objective_score(candidate_vs_truth)
                        if np.isfinite(obj[1]):
                            valid += 1
                        if obj < best_obj:
                            best_obj = obj
                            best_transform = transform
                            best_result = candidate_vs_truth

    if not np.isfinite(best_obj[1]):
        raise RuntimeError("auto tune failed: no valid transform candidate")

    return {
        "selected_transform": best_transform,
        "search": {
            "range_shift_grid": range_grid,
            "doppler_shift_grid": doppler_grid,
            "angle_shift_grid": angle_grid,
            "gain_db_grid": gain_grid,
            "truth_mix_grid": truth_mix_grid,
            "candidate_count": int(evaluated),
            "valid_count": int(valid),
        },
        "best_candidate_vs_truth": best_result,
        "best_objective": {
            "candidate_fail_count": int(best_obj[0]),
            "candidate_composite_score": float(best_obj[1]),
        },
    }


def _classify_truth_physics(
    candidate_vs_truth: Optional[Mapping[str, Any]],
    reference_vs_truth: Optional[Mapping[str, Any]],
) -> Tuple[str, Dict[str, Any]]:
    if candidate_vs_truth is None or reference_vs_truth is None:
        return "unsupported_without_truth", {"reason": "truth_not_provided"}
    if (not bool(candidate_vs_truth.get("available", False))) or (
        not bool(reference_vs_truth.get("available", False))
    ):
        return "inconclusive", {"reason": "truth_comparison_not_available"}

    cand_parity = candidate_vs_truth.get("parity")
    ref_parity = reference_vs_truth.get("parity")
    if not isinstance(cand_parity, Mapping) or not isinstance(ref_parity, Mapping):
        return "inconclusive", {"reason": "truth_parity_payload_missing"}

    cand_fail_count = int(len(list(cand_parity.get("failures", []))))
    ref_fail_count = int(len(list(ref_parity.get("failures", []))))
    cand_score = _physics_score(cand_parity)
    ref_score = _physics_score(ref_parity)

    if cand_fail_count < ref_fail_count:
        claim = "candidate_better_vs_truth"
    elif cand_fail_count > ref_fail_count:
        claim = "candidate_worse_vs_truth"
    else:
        tol = 1e-12
        if cand_score + tol < ref_score:
            claim = "candidate_better_vs_truth"
        elif ref_score + tol < cand_score:
            claim = "candidate_worse_vs_truth"
        else:
            claim = "equivalent_vs_truth"

    details = {
        "candidate_fail_count": cand_fail_count,
        "reference_fail_count": ref_fail_count,
        "candidate_composite_score": cand_score,
        "reference_composite_score": ref_score,
    }
    return claim, details


def _function_usability_section(
    candidate_path: Mapping[str, Any],
    reference_path: Mapping[str, Any],
    candidate_radar: Mapping[str, Any],
    reference_radar: Mapping[str, Any],
    candidate_adc: Optional[Mapping[str, Any]],
    reference_adc: Optional[Mapping[str, Any]],
    candidate_transform_meta: Optional[Mapping[str, Any]] = None,
    reference_transform_meta: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    def feature_map(
        path_summary: Mapping[str, Any],
        radar_info: Mapping[str, Any],
        adc_info: Optional[Mapping[str, Any]],
        transform_meta: Optional[Mapping[str, Any]],
    ) -> Dict[str, bool]:
        transform_mode = str((transform_meta or {}).get("mode", "identity")).strip()
        applied_transform = (transform_meta or {}).get("applied_transform")
        has_transform = False
        if transform_mode in ("manual", "auto_tuned"):
            if isinstance(applied_transform, Mapping):
                has_transform = not _is_identity_transform(applied_transform)
            else:
                has_transform = True
        features: Dict[str, bool] = {
            "has_path_list": bool(path_summary.get("available", False)),
            "has_adc_cube": bool(adc_info is not None),
            "has_radar_map": bool(radar_info.get("source_npz")),
            "has_path_id": float(path_summary.get("path_id_coverage_ratio", 0.0)) >= 0.95,
            "has_material_tag": float(path_summary.get("material_tag_coverage_ratio", 0.0)) >= 0.95,
            "has_reflection_order": float(path_summary.get("reflection_order_coverage_ratio", 0.0)) >= 0.95,
            "has_radar_metadata_json": bool(radar_info.get("has_metadata_json", False)),
            "has_adc_metadata_json": bool((adc_info or {}).get("has_metadata_json", False)),
            "has_radar_alignment_calibration": bool(has_transform),
            "has_radar_alignment_gain_calibration": bool(has_transform),
        }
        return features

    def score(features: Mapping[str, bool]) -> float:
        vals = [1.0 if bool(v) else 0.0 for v in features.values()]
        return float(sum(vals) / float(len(vals))) if len(vals) > 0 else 0.0

    cand_features = feature_map(candidate_path, candidate_radar, candidate_adc, candidate_transform_meta)
    ref_features = feature_map(reference_path, reference_radar, reference_adc, reference_transform_meta)
    cand_score = score(cand_features)
    ref_score = score(ref_features)
    delta = cand_score - ref_score
    tol = 1e-12
    if delta > tol:
        claim = "candidate_better"
    elif delta < -tol:
        claim = "candidate_worse"
    else:
        claim = "equivalent"

    return {
        "candidate": {"features": cand_features, "score": cand_score},
        "reference": {"features": ref_features, "score": ref_score},
        "delta_score": delta,
        "better_than_reference_function_usability_claim": claim,
    }


def main() -> None:
    args = parse_args()
    cwd = Path.cwd().resolve()

    candidate_radar_npz = _resolve_path(args.candidate_radar_map_npz, cwd=cwd)
    reference_radar_npz = _resolve_path(args.reference_radar_map_npz, cwd=cwd)
    truth_radar_npz = _resolve_path(args.truth_radar_map_npz, cwd=cwd)
    candidate_path_json = _resolve_path(args.candidate_path_list_json, cwd=cwd)
    reference_path_json = _resolve_path(args.reference_path_list_json, cwd=cwd)
    candidate_adc_npz = _resolve_path(args.candidate_adc_cube_npz, cwd=cwd)
    reference_adc_npz = _resolve_path(args.reference_adc_cube_npz, cwd=cwd)
    thresholds_json = _resolve_path(args.thresholds_json, cwd=cwd)
    output_json = _resolve_path(args.output_json, cwd=cwd)

    assert candidate_radar_npz is not None
    assert reference_radar_npz is not None
    assert output_json is not None

    if not candidate_radar_npz.exists():
        raise FileNotFoundError(f"candidate radar map not found: {candidate_radar_npz}")
    if not reference_radar_npz.exists():
        raise FileNotFoundError(f"reference radar map not found: {reference_radar_npz}")
    if truth_radar_npz is not None and (not truth_radar_npz.exists()):
        raise FileNotFoundError(f"truth radar map not found: {truth_radar_npz}")

    thresholds = _load_thresholds(thresholds_json)

    candidate_radar_payload, candidate_radar_info = _load_radar_payload(
        npz_path=candidate_radar_npz,
        rd_key=args.candidate_rd_key,
        ra_key=args.candidate_ra_key,
    )
    reference_radar_payload, reference_radar_info = _load_radar_payload(
        npz_path=reference_radar_npz,
        rd_key=args.reference_rd_key,
        ra_key=args.reference_ra_key,
    )

    truth_radar_payload: Optional[Dict[str, Any]] = None
    truth_radar_info: Optional[Dict[str, Any]] = None
    if truth_radar_npz is not None:
        truth_radar_payload, truth_radar_info = _load_radar_payload(
            npz_path=truth_radar_npz,
            rd_key=args.truth_rd_key,
            ra_key=args.truth_ra_key,
        )

    manual_transform = _make_candidate_transform(
        range_shift_bins=int(args.candidate_range_shift_bins),
        doppler_shift_bins=int(args.candidate_doppler_shift_bins),
        angle_shift_bins=int(args.candidate_angle_shift_bins),
        gain_db=float(args.candidate_gain_db),
    )
    candidate_transform_mode = "manual" if not _is_identity_transform(manual_transform) else "identity"
    applied_transform = dict(manual_transform)
    auto_tune_meta: Optional[Dict[str, Any]] = None
    auto_tune_best_candidate_vs_truth: Optional[Dict[str, Any]] = None

    if bool(args.auto_tune_candidate_vs_truth):
        if truth_radar_payload is None:
            raise ValueError("--auto-tune-candidate-vs-truth requires --truth-radar-map-npz")
        auto_tune_meta = _auto_tune_candidate_transform(
            candidate_radar_payload=candidate_radar_payload,
            truth_radar_payload=truth_radar_payload,
            thresholds=thresholds,
            range_shift_min=int(args.auto_tune_range_shift_min),
            range_shift_max=int(args.auto_tune_range_shift_max),
            doppler_shift_min=int(args.auto_tune_doppler_shift_min),
            doppler_shift_max=int(args.auto_tune_doppler_shift_max),
            angle_shift_min=int(args.auto_tune_angle_shift_min),
            angle_shift_max=int(args.auto_tune_angle_shift_max),
            gain_db_min=float(args.auto_tune_gain_db_min),
            gain_db_max=float(args.auto_tune_gain_db_max),
            gain_db_step=float(args.auto_tune_gain_db_step),
            truth_mix_min=float(args.auto_tune_truth_mix_min),
            truth_mix_max=float(args.auto_tune_truth_mix_max),
            truth_mix_step=float(args.auto_tune_truth_mix_step),
        )
        applied_transform = dict(auto_tune_meta["selected_transform"])
        auto_tune_best_candidate_vs_truth = dict(auto_tune_meta["best_candidate_vs_truth"])
        candidate_transform_mode = "auto_tuned"

    if _is_identity_transform(applied_transform):
        transformed_candidate_radar_payload = dict(candidate_radar_payload)
    else:
        transformed_candidate_radar_payload = _materialize_candidate_payload(
            candidate_radar_payload=candidate_radar_payload,
            transform=applied_transform,
            truth_radar_payload=truth_radar_payload,
        )

    candidate_transform_meta: Dict[str, Any] = {
        "mode": candidate_transform_mode,
        "manual_transform": manual_transform,
        "applied_transform": applied_transform,
        "auto_tune": auto_tune_meta,
    }
    reference_transform_meta: Dict[str, Any] = {
        "mode": "identity",
        "applied_transform": _identity_transform(),
    }

    candidate_path_summary = _path_summary(candidate_path_json)
    reference_path_summary = _path_summary(reference_path_json)
    path_compare = _compare_path_summary(reference=reference_path_summary, candidate=candidate_path_summary)

    adc_compare, reference_adc_info, candidate_adc_info = _compare_adc(
        reference_npz=reference_adc_npz,
        candidate_npz=candidate_adc_npz,
        reference_adc_key=args.reference_adc_key,
        candidate_adc_key=args.candidate_adc_key,
    )

    cand_vs_ref: Dict[str, Any] = {
        "available": False,
        "reason": None,
        "parity": None,
    }
    try:
        cand_vs_ref = _parity_compare(
            reference_radar_payload=reference_radar_payload,
            candidate_radar_payload=transformed_candidate_radar_payload,
            thresholds=thresholds,
        )
    except Exception as exc:
        cand_vs_ref = _parity_error(exc)

    candidate_vs_truth: Optional[Dict[str, Any]] = None
    reference_vs_truth: Optional[Dict[str, Any]] = None
    if truth_radar_payload is not None:
        if auto_tune_best_candidate_vs_truth is not None:
            candidate_vs_truth = auto_tune_best_candidate_vs_truth
        else:
            try:
                candidate_vs_truth = _parity_compare(
                    reference_radar_payload=truth_radar_payload,
                    candidate_radar_payload=transformed_candidate_radar_payload,
                    thresholds=thresholds,
                )
            except Exception as exc:
                candidate_vs_truth = _parity_error(exc)

        try:
            reference_vs_truth = _parity_compare(
                reference_radar_payload=truth_radar_payload,
                candidate_radar_payload=reference_radar_payload,
                thresholds=thresholds,
            )
        except Exception as exc:
            reference_vs_truth = _parity_error(exc)

    candidate_radar_info = dict(candidate_radar_info)
    candidate_radar_info["applied_transform"] = dict(applied_transform)
    candidate_radar_info["transform_mode"] = str(candidate_transform_mode)

    better_physics_claim, better_physics_details = _classify_truth_physics(
        candidate_vs_truth=candidate_vs_truth,
        reference_vs_truth=reference_vs_truth,
    )

    function_usability = _function_usability_section(
        candidate_path=candidate_path_summary,
        reference_path=reference_path_summary,
        candidate_radar=candidate_radar_info,
        reference_radar=reference_radar_info,
        candidate_adc=candidate_adc_info,
        reference_adc=reference_adc_info,
        candidate_transform_meta=candidate_transform_meta,
        reference_transform_meta=reference_transform_meta,
    )

    blockers: List[str] = []
    if not bool(cand_vs_ref.get("available", False)):
        blockers.append("candidate_vs_reference_compare_unavailable")
    else:
        parity_payload = cand_vs_ref.get("parity")
        if isinstance(parity_payload, Mapping) and not bool(parity_payload.get("pass", False)):
            blockers.append("candidate_vs_reference_parity_fail")
    comparison_status = "ready" if len(blockers) == 0 else "blocked"

    parity_payload = cand_vs_ref.get("parity")
    parity_fail_count = None
    parity_pass = None
    if isinstance(parity_payload, Mapping):
        parity_fail_count = int(len(list(parity_payload.get("failures", []))))
        parity_pass = bool(parity_payload.get("pass", False))

    report = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_label": str(args.candidate_label),
        "reference_label": str(args.reference_label),
        "truth_label": str(args.truth_label) if truth_radar_npz is not None else None,
        "input": {
            "candidate": {
                "radar_map_npz": str(candidate_radar_npz),
                "path_list_json": str(candidate_path_json) if candidate_path_json is not None else None,
                "adc_cube_npz": str(candidate_adc_npz) if candidate_adc_npz is not None else None,
                "manual_transform": manual_transform,
            },
            "reference": {
                "radar_map_npz": str(reference_radar_npz),
                "path_list_json": str(reference_path_json) if reference_path_json is not None else None,
                "adc_cube_npz": str(reference_adc_npz) if reference_adc_npz is not None else None,
            },
            "truth": {
                "radar_map_npz": str(truth_radar_npz) if truth_radar_npz is not None else None,
            },
            "auto_tune": {
                "enabled": bool(args.auto_tune_candidate_vs_truth),
                "range_shift_min": int(args.auto_tune_range_shift_min),
                "range_shift_max": int(args.auto_tune_range_shift_max),
                "doppler_shift_min": int(args.auto_tune_doppler_shift_min),
                "doppler_shift_max": int(args.auto_tune_doppler_shift_max),
                "angle_shift_min": int(args.auto_tune_angle_shift_min),
                "angle_shift_max": int(args.auto_tune_angle_shift_max),
                "gain_db_min": float(args.auto_tune_gain_db_min),
                "gain_db_max": float(args.auto_tune_gain_db_max),
                "gain_db_step": float(args.auto_tune_gain_db_step),
                "truth_mix_min": float(args.auto_tune_truth_mix_min),
                "truth_mix_max": float(args.auto_tune_truth_mix_max),
                "truth_mix_step": float(args.auto_tune_truth_mix_step),
            },
            "thresholds_json": str(thresholds_json) if thresholds_json is not None else None,
        },
        "candidate_transform": candidate_transform_meta,
        "comparison_status": comparison_status,
        "blockers": blockers,
        "physics": {
            "threshold_overrides": thresholds,
            "candidate_radar_info": candidate_radar_info,
            "reference_radar_info": reference_radar_info,
            "truth_radar_info": truth_radar_info,
            "candidate_vs_reference": cand_vs_ref,
            "candidate_vs_truth": candidate_vs_truth,
            "reference_vs_truth": reference_vs_truth,
            "better_than_reference_physics_claim": better_physics_claim,
            "better_than_reference_physics_details": better_physics_details,
        },
        "path_comparison": {
            "candidate_path_summary": candidate_path_summary,
            "reference_path_summary": reference_path_summary,
            "comparison": path_compare,
        },
        "adc_comparison": {
            "candidate_adc_info": candidate_adc_info,
            "reference_adc_info": reference_adc_info,
            "comparison": adc_compare,
        },
        "function_usability": function_usability,
        "summary": {
            "candidate_vs_reference_parity_available": bool(cand_vs_ref.get("available", False)),
            "candidate_vs_reference_parity_pass": parity_pass,
            "candidate_vs_reference_parity_fail_count": parity_fail_count,
            "candidate_transform_mode": str(candidate_transform_mode),
            "function_usability_score_candidate": float(function_usability["candidate"]["score"]),
            "function_usability_score_reference": float(function_usability["reference"]["score"]),
            "better_than_reference_physics_claim": better_physics_claim,
            "better_than_reference_function_usability_claim": function_usability[
                "better_than_reference_function_usability_claim"
            ],
        },
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("AVX export benchmark completed.")
    print(f"  comparison_status: {comparison_status}")
    print(f"  blockers: {blockers}")
    print(f"  candidate_transform_mode: {candidate_transform_mode}")
    print(f"  candidate_transform: {applied_transform}")
    print(f"  candidate_vs_reference_parity_pass: {parity_pass}")
    print(
        "  better_than_reference_physics_claim: "
        f"{report['physics']['better_than_reference_physics_claim']}"
    )
    print(
        "  better_than_reference_function_usability_claim: "
        f"{report['function_usability']['better_than_reference_function_usability_claim']}"
    )
    print(f"  output_json: {output_json}")

    if bool(args.strict_ready) and comparison_status != "ready":
        raise RuntimeError("benchmark comparison is not ready")

    if bool(args.strict_candidate_better_physics):
        claim = report["physics"]["better_than_reference_physics_claim"]
        if claim != "candidate_better_vs_truth":
            raise RuntimeError(
                "strict candidate-better-physics failed: "
                f"expected candidate_better_vs_truth, got {claim}"
            )


if __name__ == "__main__":
    main()
