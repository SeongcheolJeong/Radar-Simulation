import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

import numpy as np

from ..types import Path as RadarPath


def load_sionna_paths_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("sionna paths json must be object")
    return dict(payload)


def adapt_sionna_paths_payload_to_paths_by_chirp(
    payload: Mapping[str, Any],
    n_chirps: int,
) -> List[List[RadarPath]]:
    if int(n_chirps) <= 0:
        raise ValueError("n_chirps must be positive")

    if "paths_by_chirp" in payload:
        return _adapt_paths_by_chirp_payload(payload["paths_by_chirp"], n_chirps=int(n_chirps))
    if "paths" in payload:
        return _adapt_flat_paths_payload(payload["paths"], n_chirps=int(n_chirps))
    raise ValueError("sionna payload must include paths_by_chirp or paths")


def _adapt_paths_by_chirp_payload(raw: Any, n_chirps: int) -> List[List[RadarPath]]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("paths_by_chirp must be list")
    if len(raw) != int(n_chirps):
        raise ValueError("paths_by_chirp length must equal n_chirps")

    out: List[List[RadarPath]] = []
    for chirp_idx, chirp_paths in enumerate(raw):
        if not isinstance(chirp_paths, Sequence) or isinstance(chirp_paths, (str, bytes)):
            raise ValueError(f"paths_by_chirp[{chirp_idx}] must be list")
        out.append([_adapt_single_path(item, chirp_idx=chirp_idx, path_idx=i) for i, item in enumerate(chirp_paths)])
    return out


def _adapt_flat_paths_payload(raw: Any, n_chirps: int) -> List[List[RadarPath]]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("paths must be list")

    out: List[List[RadarPath]] = [[] for _ in range(int(n_chirps))]
    for path_idx, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise ValueError(f"paths[{path_idx}] must be object")
        chirp_idx = int(item.get("chirp_idx", item.get("chirp_index", item.get("k", -1))))
        if chirp_idx < 0 or chirp_idx >= int(n_chirps):
            raise ValueError(f"paths[{path_idx}] chirp index out of range: {chirp_idx}")
        out[chirp_idx].append(_adapt_single_path(item, chirp_idx=chirp_idx, path_idx=path_idx))
    return out


def _adapt_single_path(
    item: Mapping[str, Any],
    chirp_idx: int,
    path_idx: int,
) -> RadarPath:
    delay_s = float(item["delay_s"])
    doppler_hz = float(item.get("doppler_hz", item.get("fd_hz", 0.0)))

    if "unit_direction" in item:
        unit_direction = _parse_unit_direction(item["unit_direction"])
    elif "u" in item:
        unit_direction = _parse_unit_direction(item["u"])
    else:
        az = float(item.get("az_rad", 0.0))
        el = float(item.get("el_rad", 0.0))
        unit_direction = (
            float(np.cos(el) * np.cos(az)),
            float(np.cos(el) * np.sin(az)),
            float(np.sin(el)),
        )

    amp = _parse_complex(
        item.get("amp_complex", item.get("amp", item.get("complex_gain", 1.0))),
        key_name=f"path[{path_idx}].amp",
    )
    path_id = str(item.get("path_id", f"sionna_c{int(chirp_idx):04d}_p{int(path_idx):06d}"))
    material_tag = str(item.get("material_tag", item.get("material", "sionna_rt")))
    reflection_order = int(item.get("reflection_order", item.get("order", 1)))
    if reflection_order < 0:
        raise ValueError(f"path[{path_idx}].reflection_order must be >= 0")

    pol_matrix = None
    if "pol_matrix" in item:
        pol_matrix = _parse_pol_matrix(item["pol_matrix"], key_name=f"path[{path_idx}].pol_matrix")

    return RadarPath(
        delay_s=delay_s,
        doppler_hz=doppler_hz,
        unit_direction=unit_direction,
        amp=amp,
        pol_matrix=pol_matrix,
        path_id=path_id,
        material_tag=material_tag,
        reflection_order=reflection_order,
    )


def _parse_unit_direction(value: Any) -> tuple:
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
