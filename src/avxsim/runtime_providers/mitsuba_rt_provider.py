from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from ..constants import C0


def generate_sionna_like_paths_from_mitsuba(context: Mapping[str, Any]) -> Dict[str, Any]:
    n_chirps = int(context.get("n_chirps", 1))
    if n_chirps <= 0:
        raise ValueError("context.n_chirps must be positive")

    runtime_input = _as_obj(context, "runtime_input", required=False)
    ego_origin = _vec3(runtime_input.get("ego_origin_m", [0.0, 0.0, 0.0]), "runtime_input.ego_origin_m")
    spheres_raw = runtime_input.get("spheres")
    if not isinstance(spheres_raw, Sequence) or isinstance(spheres_raw, (str, bytes)):
        raise ValueError("runtime_input.spheres must be a non-empty list")
    if len(spheres_raw) == 0:
        raise ValueError("runtime_input.spheres must be a non-empty list")

    fc_hz = float(context.get("fc_hz", 77e9))
    lam = C0 / fc_hz
    chirp_interval_s = float(runtime_input.get("chirp_interval_s", 4.0e-5))
    min_range_m = max(float(runtime_input.get("min_range_m", 0.1)), 1e-6)

    mi = _import_mitsuba()
    scene = _build_mitsuba_scene(mi=mi, spheres=spheres_raw)

    spheres = [_normalize_sphere_entry(item, idx=i) for i, item in enumerate(spheres_raw)]
    out: List[List[Dict[str, Any]]] = []
    for chirp_idx in range(n_chirps):
        t = float(chirp_idx) * float(chirp_interval_s)
        chirp_paths: List[Dict[str, Any]] = []
        for i, sphere in enumerate(spheres):
            center0 = sphere["center_m"]
            vel = sphere["velocity_mps"]
            center_t = center0 + vel * t
            rel = center_t - ego_origin
            norm = float(np.linalg.norm(rel))
            if norm <= 0.0:
                continue
            u = rel / norm
            ray = mi.Ray3f(o=[float(ego_origin[0]), float(ego_origin[1]), float(ego_origin[2])], d=[float(u[0]), float(u[1]), float(u[2])], time=0.0, wavelengths=[])
            si = scene.ray_intersect(ray)
            if not bool(si.is_valid()):
                continue
            one_way_range = max(float(si.t), float(min_range_m))
            radial_velocity = float(np.dot(vel, u))
            doppler_hz = float(2.0 * radial_velocity / lam)

            amp0 = complex(sphere["amp"])
            range_amp_exponent = float(sphere["range_amp_exponent"])
            amp = amp0 / (one_way_range ** max(range_amp_exponent, 0.0))

            chirp_paths.append(
                {
                    "delay_s": float(2.0 * one_way_range / C0),
                    "doppler_hz": doppler_hz,
                    "unit_direction": [float(u[0]), float(u[1]), float(u[2])],
                    "amp_complex": {"re": float(np.real(amp)), "im": float(np.imag(amp))},
                    "path_id": str(sphere["path_id_prefix"]) + f"_c{int(chirp_idx):04d}",
                    "material_tag": str(sphere["material_tag"]),
                    "reflection_order": int(sphere["reflection_order"]),
                }
            )
        out.append(chirp_paths)
    return {"paths_by_chirp": out}


def _build_mitsuba_scene(mi: Any, spheres: Sequence[Any]) -> Any:
    scene_dict: Dict[str, Any] = {"type": "scene"}
    for i, item in enumerate(spheres):
        entry = _normalize_sphere_entry(item, idx=i)
        center = entry["center_m"]
        scene_dict[f"sphere_{i:03d}"] = {
            "type": "sphere",
            "center": [float(center[0]), float(center[1]), float(center[2])],
            "radius": float(entry["radius_m"]),
            "bsdf": {"type": "diffuse"},
        }
    return mi.load_dict(scene_dict)


def _normalize_sphere_entry(item: Any, idx: int) -> Dict[str, Any]:
    if not isinstance(item, Mapping):
        raise ValueError(f"runtime_input.spheres[{idx}] must be object")
    center_m = _vec3(item.get("center_m"), f"runtime_input.spheres[{idx}].center_m")
    radius_m = float(item.get("radius_m", 0.5))
    if radius_m <= 0.0:
        raise ValueError(f"runtime_input.spheres[{idx}].radius_m must be positive")
    velocity_mps = _vec3(item.get("velocity_mps", [0.0, 0.0, 0.0]), f"runtime_input.spheres[{idx}].velocity_mps")
    amp = _parse_complex(item.get("amp", 1.0), f"runtime_input.spheres[{idx}].amp")
    range_amp_exponent = float(item.get("range_amp_exponent", 2.0))
    reflection_order = int(item.get("reflection_order", 1))
    if reflection_order < 0:
        raise ValueError(f"runtime_input.spheres[{idx}].reflection_order must be >= 0")
    return {
        "center_m": center_m,
        "radius_m": radius_m,
        "velocity_mps": velocity_mps,
        "amp": amp,
        "range_amp_exponent": range_amp_exponent,
        "path_id_prefix": str(item.get("path_id_prefix", f"mitsuba_sphere_{idx:03d}")),
        "material_tag": str(item.get("material_tag", "mitsuba_rt")),
        "reflection_order": reflection_order,
    }


def _import_mitsuba() -> Any:
    try:
        import mitsuba as mi  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"mitsuba import failed: {exc}") from exc
    variant = _pick_variant(mi)
    try:
        mi.set_variant(variant)
    except Exception as exc:
        raise RuntimeError(f"mitsuba.set_variant({variant}) failed: {exc}") from exc
    return mi


def _pick_variant(mi: Any) -> str:
    preferred = ("scalar_rgb", "llvm_ad_rgb")
    available = tuple(str(x) for x in mi.variants())
    for cand in preferred:
        if cand in available:
            return cand
    if len(available) == 0:
        raise RuntimeError("mitsuba has no available variants")
    return available[0]


def _vec3(value: Any, key_name: str) -> np.ndarray:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{key_name} must be [x,y,z]")
    if len(value) != 3:
        raise ValueError(f"{key_name} must have length 3")
    arr = np.asarray(value, dtype=np.float64).reshape(3)
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{key_name} must be finite")
    return arr


def _as_obj(payload: Mapping[str, Any], key: str, required: bool = True) -> Dict[str, Any]:
    value = payload.get(key)
    if value is None and not required:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be object")
    return dict(value)


def _parse_complex(value: Any, key_name: str) -> complex:
    if isinstance(value, Mapping):
        re = float(value.get("re", 0.0))
        im = float(value.get("im", 0.0))
        return complex(re, im)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if len(value) != 2:
            raise ValueError(f"{key_name} sequence form must be [re, im]")
        return complex(float(value[0]), float(value[1]))
    return complex(float(value), 0.0)
