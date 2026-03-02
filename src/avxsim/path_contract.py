from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np

from .types import Path as RadarPath


def validate_paths_by_chirp(
    paths_by_chirp: Sequence[Sequence[RadarPath]],
    n_chirps: Optional[int] = None,
    require_metadata: bool = False,
    unit_norm_tolerance: float = 1e-3,
) -> Dict[str, int]:
    if float(unit_norm_tolerance) < 0.0:
        raise ValueError("unit_norm_tolerance must be >= 0")
    _validate_paths_container(
        paths_by_chirp=paths_by_chirp,
        n_chirps=n_chirps,
    )

    path_count = 0
    for chirp_idx, chirp_paths in enumerate(paths_by_chirp):
        for path_idx, p in enumerate(chirp_paths):
            if not isinstance(p, RadarPath):
                raise ValueError(f"paths_by_chirp[{chirp_idx}][{path_idx}] must be avxsim.types.Path")
            _validate_delay_s(
                delay_s=p.delay_s,
                field_name=f"paths_by_chirp[{chirp_idx}][{path_idx}].delay_s",
            )
            _validate_finite_scalar(
                value=p.doppler_hz,
                field_name=f"paths_by_chirp[{chirp_idx}][{path_idx}].doppler_hz",
            )
            _validate_unit_direction(
                unit_direction=p.unit_direction,
                field_name=f"paths_by_chirp[{chirp_idx}][{path_idx}].unit_direction",
                unit_norm_tolerance=float(unit_norm_tolerance),
            )
            _validate_complex(
                value=p.amp,
                field_name=f"paths_by_chirp[{chirp_idx}][{path_idx}].amp",
            )
            if p.pol_matrix is not None:
                _validate_pol_matrix(
                    value=p.pol_matrix,
                    field_name=f"paths_by_chirp[{chirp_idx}][{path_idx}].pol_matrix",
                )
            _validate_optional_metadata_fields(
                path_id=p.path_id,
                material_tag=p.material_tag,
                reflection_order=p.reflection_order,
                require_metadata=bool(require_metadata),
                field_prefix=f"paths_by_chirp[{chirp_idx}][{path_idx}]",
            )
            path_count += 1

    return {"chirp_count": int(len(paths_by_chirp)), "path_count": int(path_count)}


def validate_paths_payload_json(
    payload: Any,
    expected_n_chirps: Optional[int] = None,
    require_metadata: bool = False,
    unit_norm_tolerance: float = 1e-3,
) -> Dict[str, int]:
    _validate_paths_container(paths_by_chirp=payload, n_chirps=expected_n_chirps)
    path_count = 0
    for chirp_idx, chirp_paths in enumerate(payload):
        for path_idx, item in enumerate(chirp_paths):
            if not isinstance(item, Mapping):
                raise ValueError(f"paths_by_chirp[{chirp_idx}][{path_idx}] must be object")
            _validate_delay_s(
                delay_s=item.get("delay_s"),
                field_name=f"paths_by_chirp[{chirp_idx}][{path_idx}].delay_s",
            )
            _validate_finite_scalar(
                value=item.get("doppler_hz"),
                field_name=f"paths_by_chirp[{chirp_idx}][{path_idx}].doppler_hz",
            )
            _validate_unit_direction(
                unit_direction=item.get("unit_direction"),
                field_name=f"paths_by_chirp[{chirp_idx}][{path_idx}].unit_direction",
                unit_norm_tolerance=float(unit_norm_tolerance),
            )
            _validate_payload_amp(
                item=item,
                field_name=f"paths_by_chirp[{chirp_idx}][{path_idx}]",
            )
            if "pol_matrix" in item:
                _validate_pol_matrix(
                    value=item.get("pol_matrix"),
                    field_name=f"paths_by_chirp[{chirp_idx}][{path_idx}].pol_matrix",
                )
            _validate_optional_metadata_fields(
                path_id=item.get("path_id"),
                material_tag=item.get("material_tag"),
                reflection_order=item.get("reflection_order"),
                require_metadata=bool(require_metadata),
                field_prefix=f"paths_by_chirp[{chirp_idx}][{path_idx}]",
            )
            path_count += 1
    return {"chirp_count": int(len(payload)), "path_count": int(path_count)}


def _validate_paths_container(
    paths_by_chirp: Any,
    n_chirps: Optional[int],
) -> None:
    if (not isinstance(paths_by_chirp, Sequence)) or isinstance(paths_by_chirp, (str, bytes)):
        raise ValueError("paths_by_chirp must be list")
    if n_chirps is not None and len(paths_by_chirp) != int(n_chirps):
        raise ValueError("paths_by_chirp length must match chirp count")
    for chirp_idx, chirp_paths in enumerate(paths_by_chirp):
        if (not isinstance(chirp_paths, Sequence)) or isinstance(chirp_paths, (str, bytes)):
            raise ValueError(f"paths_by_chirp[{chirp_idx}] must be list")


def _validate_delay_s(delay_s: Any, field_name: str) -> None:
    if delay_s is None:
        raise ValueError(f"{field_name} is required")
    value = float(delay_s)
    if not np.isfinite(value):
        raise ValueError(f"{field_name} must be finite")
    if value <= 0.0:
        raise ValueError(f"{field_name} must be > 0")


def _validate_finite_scalar(value: Any, field_name: str) -> None:
    if value is None:
        raise ValueError(f"{field_name} is required")
    x = float(value)
    if not np.isfinite(x):
        raise ValueError(f"{field_name} must be finite")


def _validate_unit_direction(unit_direction: Any, field_name: str, unit_norm_tolerance: float) -> None:
    if (not isinstance(unit_direction, Sequence)) or isinstance(unit_direction, (str, bytes)):
        raise ValueError(f"{field_name} must be [ux,uy,uz]")
    if len(unit_direction) != 3:
        raise ValueError(f"{field_name} must have length 3")
    arr = np.asarray(unit_direction, dtype=np.float64).reshape(3)
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{field_name} must be finite")
    norm = float(np.linalg.norm(arr))
    if norm <= 0.0:
        raise ValueError(f"{field_name} norm must be > 0")
    if abs(norm - 1.0) > float(unit_norm_tolerance):
        raise ValueError(f"{field_name} norm must be ~= 1.0 (got {norm})")


def _validate_complex(value: Any, field_name: str) -> None:
    c = complex(value)
    if not np.isfinite(float(np.real(c))) or not np.isfinite(float(np.imag(c))):
        raise ValueError(f"{field_name} must be finite complex")


def _validate_payload_amp(item: Mapping[str, Any], field_name: str) -> None:
    if "amp_complex" in item:
        _parse_complex_from_payload(item["amp_complex"], key_name=f"{field_name}.amp_complex")
        return
    if "amp" in item:
        _parse_complex_from_payload(item["amp"], key_name=f"{field_name}.amp")
        return
    raise ValueError(f"{field_name} requires one of: amp_complex, amp")


def _validate_pol_matrix(value: Any, field_name: str) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be list of 4 complex entries")
    if len(value) != 4:
        raise ValueError(f"{field_name} must have 4 entries")
    for i, entry in enumerate(value):
        _parse_complex_from_payload(entry, key_name=f"{field_name}[{i}]")


def _parse_complex_from_payload(value: Any, key_name: str) -> complex:
    if isinstance(value, complex):
        out = complex(value)
    elif isinstance(value, Mapping):
        out = complex(float(value.get("re", 0.0)), float(value.get("im", 0.0)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if len(value) != 2:
            raise ValueError(f"{key_name} sequence form must be [re, im]")
        out = complex(float(value[0]), float(value[1]))
    else:
        out = complex(float(value), 0.0)
    if not np.isfinite(float(np.real(out))) or not np.isfinite(float(np.imag(out))):
        raise ValueError(f"{key_name} must be finite complex")
    return out


def _validate_optional_metadata_fields(
    path_id: Any,
    material_tag: Any,
    reflection_order: Any,
    require_metadata: bool,
    field_prefix: str,
) -> None:
    if require_metadata:
        if path_id is None or str(path_id).strip() == "":
            raise ValueError(f"{field_prefix}.path_id must be non-empty")
        if material_tag is None or str(material_tag).strip() == "":
            raise ValueError(f"{field_prefix}.material_tag must be non-empty")
        if reflection_order is None:
            raise ValueError(f"{field_prefix}.reflection_order must be set")
    if reflection_order is not None and int(reflection_order) < 0:
        raise ValueError(f"{field_prefix}.reflection_order must be >= 0")
