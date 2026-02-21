import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

import numpy as np

from ..constants import C0
from ..types import Path as RadarPath


def load_po_sbr_paths_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("po_sbr paths json must be object")
    return dict(payload)


def adapt_po_sbr_paths_payload_to_paths_by_chirp(
    payload: Mapping[str, Any],
    n_chirps: int,
    fc_hz: float,
) -> List[List[RadarPath]]:
    if int(n_chirps) <= 0:
        raise ValueError("n_chirps must be positive")
    if float(fc_hz) <= 0.0:
        raise ValueError("fc_hz must be > 0")

    if "paths_by_chirp" in payload:
        return _adapt_paths_by_chirp_payload(payload["paths_by_chirp"], n_chirps=int(n_chirps), fc_hz=float(fc_hz))
    if "paths" in payload:
        return _adapt_flat_paths_payload(payload["paths"], n_chirps=int(n_chirps), fc_hz=float(fc_hz))
    raise ValueError("po_sbr payload must include paths_by_chirp or paths")


def _adapt_paths_by_chirp_payload(raw: Any, n_chirps: int, fc_hz: float) -> List[List[RadarPath]]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("paths_by_chirp must be list")
    if len(raw) != int(n_chirps):
        raise ValueError("paths_by_chirp length must equal n_chirps")

    out: List[List[RadarPath]] = []
    for chirp_idx, chirp_paths in enumerate(raw):
        if not isinstance(chirp_paths, Sequence) or isinstance(chirp_paths, (str, bytes)):
            raise ValueError(f"paths_by_chirp[{chirp_idx}] must be list")
        out.append(
            [
                _adapt_single_path(
                    item=item,
                    chirp_idx=chirp_idx,
                    path_idx=i,
                    fc_hz=float(fc_hz),
                )
                for i, item in enumerate(chirp_paths)
            ]
        )
    return out


def _adapt_flat_paths_payload(raw: Any, n_chirps: int, fc_hz: float) -> List[List[RadarPath]]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("paths must be list")

    out: List[List[RadarPath]] = [[] for _ in range(int(n_chirps))]
    for path_idx, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise ValueError(f"paths[{path_idx}] must be object")
        chirp_idx = int(item.get("chirp_idx", item.get("chirp_index", item.get("k", -1))))
        if chirp_idx < 0 or chirp_idx >= int(n_chirps):
            raise ValueError(f"paths[{path_idx}] chirp index out of range: {chirp_idx}")
        out[chirp_idx].append(
            _adapt_single_path(
                item=item,
                chirp_idx=chirp_idx,
                path_idx=path_idx,
                fc_hz=float(fc_hz),
            )
        )
    return out


def _adapt_single_path(
    item: Mapping[str, Any],
    chirp_idx: int,
    path_idx: int,
    fc_hz: float,
) -> RadarPath:
    delay_s = _parse_delay_seconds(item)
    doppler_hz = _parse_doppler_hz(item, fc_hz=float(fc_hz))
    unit_direction = _parse_unit_direction(item)
    amp = _parse_amplitude_complex(item, path_idx=path_idx)

    path_id = str(item.get("path_id", f"po_sbr_c{int(chirp_idx):04d}_p{int(path_idx):06d}"))
    material_tag = str(item.get("material_tag", item.get("material", "po_sbr")))
    reflection_order = int(item.get("reflection_order", item.get("bounce_count", 1)))
    if reflection_order < 0:
        raise ValueError(f"path[{path_idx}].reflection_order must be >= 0")

    pol_matrix = None
    if "pol_matrix" in item:
        pol_matrix = _parse_pol_matrix(item["pol_matrix"], key_name=f"path[{path_idx}].pol_matrix")

    return RadarPath(
        delay_s=float(delay_s),
        doppler_hz=float(doppler_hz),
        unit_direction=unit_direction,
        amp=complex(amp),
        pol_matrix=pol_matrix,
        path_id=path_id,
        material_tag=material_tag,
        reflection_order=reflection_order,
    )


def _parse_delay_seconds(item: Mapping[str, Any]) -> float:
    if "delay_s" in item:
        delay = float(item["delay_s"])
        if delay <= 0.0:
            raise ValueError("delay_s must be > 0")
        return delay

    if "range_m" in item:
        range_m = float(item["range_m"])
        if range_m <= 0.0:
            raise ValueError("range_m must be > 0")
        range_mode = str(item.get("range_mode", "one_way")).strip().lower()
        if range_mode == "one_way":
            return float(2.0 * range_m / C0)
        if range_mode == "round_trip":
            return float(range_m / C0)
        raise ValueError("range_mode must be one_way or round_trip")

    raise ValueError("path requires one of: delay_s, range_m")


def _parse_doppler_hz(item: Mapping[str, Any], fc_hz: float) -> float:
    if "doppler_hz" in item:
        return float(item["doppler_hz"])
    if "fd_hz" in item:
        return float(item["fd_hz"])
    if "radial_velocity_mps" in item:
        lam = C0 / float(fc_hz)
        return float(2.0 * float(item["radial_velocity_mps"]) / lam)
    return 0.0


def _parse_unit_direction(item: Mapping[str, Any]) -> tuple:
    if "unit_direction" in item:
        return _normalize_unit_direction(item["unit_direction"])
    if "u" in item:
        return _normalize_unit_direction(item["u"])
    if ("az_deg" in item) or ("el_deg" in item):
        az = np.deg2rad(float(item.get("az_deg", 0.0)))
        el = np.deg2rad(float(item.get("el_deg", 0.0)))
        return (
            float(np.cos(el) * np.cos(az)),
            float(np.cos(el) * np.sin(az)),
            float(np.sin(el)),
        )
    if ("az_rad" in item) or ("el_rad" in item):
        az = float(item.get("az_rad", 0.0))
        el = float(item.get("el_rad", 0.0))
        return (
            float(np.cos(el) * np.cos(az)),
            float(np.cos(el) * np.sin(az)),
            float(np.sin(el)),
        )
    raise ValueError("path requires one of: unit_direction/u, az/el")


def _normalize_unit_direction(value: Any) -> tuple:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("unit_direction must be [ux,uy,uz]")
    if len(value) != 3:
        raise ValueError("unit_direction must have length 3")
    arr = np.asarray(value, dtype=np.float64).reshape(3)
    if not np.all(np.isfinite(arr)):
        raise ValueError("unit_direction must be finite")
    norm = float(np.linalg.norm(arr))
    if norm <= 0.0:
        raise ValueError("unit_direction norm must be > 0")
    arr = arr / norm
    return (float(arr[0]), float(arr[1]), float(arr[2]))


def _parse_amplitude_complex(item: Mapping[str, Any], path_idx: int) -> complex:
    if "amp_complex" in item:
        return _parse_complex(item["amp_complex"], key_name=f"path[{path_idx}].amp_complex")
    if "amp" in item:
        return _parse_complex(item["amp"], key_name=f"path[{path_idx}].amp")
    if "complex_gain" in item:
        return _parse_complex(item["complex_gain"], key_name=f"path[{path_idx}].complex_gain")

    # Candidate PO-SBR-style physical proxy:
    # amp ~= 10^((rcs_dbsm - path_loss_db - bounce_loss_db)/20) * exp(j*phase_rad)
    path_loss_db = float(item.get("path_loss_db", 0.0))
    bounce_loss_db = float(item.get("bounce_loss_db", 0.0))
    rcs_dbsm = float(item.get("rcs_dbsm", 0.0))
    phase_rad = float(item.get("phase_rad", 0.0))
    mag = 10.0 ** ((rcs_dbsm - path_loss_db - bounce_loss_db) / 20.0)
    return complex(float(mag * np.cos(phase_rad)), float(mag * np.sin(phase_rad)))


def _parse_complex(value: Any, key_name: str) -> complex:
    if isinstance(value, Mapping):
        return complex(float(value.get("re", 0.0)), float(value.get("im", 0.0)))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if len(value) != 2:
            raise ValueError(f"{key_name} list form must be [re, im]")
        return complex(float(value[0]), float(value[1]))
    try:
        return complex(float(value), 0.0)
    except Exception as exc:
        raise ValueError(f"{key_name} must be scalar or complex map/list") from exc


def _parse_pol_matrix(value: Any, key_name: str) -> Optional[tuple]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{key_name} must be list of 4 complex entries")
    if len(value) != 4:
        raise ValueError(f"{key_name} must have 4 entries")
    out = []
    for i, entry in enumerate(value):
        out.append(_parse_complex(entry, key_name=f"{key_name}[{i}]"))
    return (out[0], out[1], out[2], out[3])
