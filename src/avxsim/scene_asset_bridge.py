import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence


def load_scene_asset_manifest_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("asset manifest json must be object")
    return payload


def save_scene_json(path: str, scene_payload: Mapping[str, Any]) -> None:
    Path(path).write_text(json.dumps(dict(scene_payload), indent=2), encoding="utf-8")


def build_mesh_scene_payload_from_asset_manifest(
    asset_manifest: Mapping[str, Any],
    scene_id: Optional[str] = None,
    n_chirps: Optional[int] = None,
    chirp_interval_s: Optional[float] = None,
    fc_hz: Optional[float] = None,
    slope_hz_per_s: Optional[float] = None,
    fs_hz: Optional[float] = None,
    samples_per_chirp: Optional[int] = None,
    default_material_tag: Optional[str] = None,
) -> Dict[str, Any]:
    sensor_mount = _as_obj(asset_manifest, "sensor_mount")
    sim_defaults = _as_obj(asset_manifest, "simulation_defaults", required=False)
    radar_defaults = _as_obj(asset_manifest, "radar", required=False)

    tx_pos_m = sensor_mount.get("tx_pos_m")
    rx_pos_m = sensor_mount.get("rx_pos_m")
    if not _is_pos_list(tx_pos_m):
        raise ValueError("sensor_mount.tx_pos_m must be list of [x,y,z]")
    if not _is_pos_list(rx_pos_m):
        raise ValueError("sensor_mount.rx_pos_m must be list of [x,y,z]")
    ego_pos_m = sensor_mount.get("ego_pos_m", [0.0, 0.0, 0.0])
    if not _is_vec3(ego_pos_m):
        raise ValueError("sensor_mount.ego_pos_m must be [x,y,z]")

    objects = _normalize_objects(
        raw_objects=asset_manifest.get("objects"),
        default_material_tag=(
            str(default_material_tag)
            if default_material_tag is not None
            else str(asset_manifest.get("default_material_tag", "default_material"))
        ),
    )
    materials = _normalize_materials(asset_manifest.get("materials"))

    resolved_scene_id = (
        str(scene_id)
        if scene_id is not None
        else str(asset_manifest.get("scene_id", "scene_from_asset_manifest"))
    )

    radar_payload = {
        "fc_hz": float(_resolve_scalar(fc_hz, radar_defaults.get("fc_hz", 77e9))),
        "slope_hz_per_s": float(
            _resolve_scalar(slope_hz_per_s, radar_defaults.get("slope_hz_per_s", 20e12))
        ),
        "fs_hz": float(_resolve_scalar(fs_hz, radar_defaults.get("fs_hz", 20e6))),
        "samples_per_chirp": int(
            _resolve_scalar(samples_per_chirp, radar_defaults.get("samples_per_chirp", 1024))
        ),
    }

    backend_payload: Dict[str, Any] = {
        "type": "mesh_material_stub",
        "n_chirps": int(_resolve_scalar(n_chirps, sim_defaults.get("n_chirps", 16))),
        "tx_pos_m": tx_pos_m,
        "rx_pos_m": rx_pos_m,
        "ego_pos_m": ego_pos_m,
        "materials": materials,
        "objects": objects,
        "range_amp_exponent": float(sim_defaults.get("range_amp_exponent", 2.0)),
        "noise_sigma": float(sim_defaults.get("noise_sigma", 0.0)),
        "default_material_tag": str(
            default_material_tag
            if default_material_tag is not None
            else asset_manifest.get("default_material_tag", "default_material")
        ),
    }
    resolved_chirp_interval = _resolve_scalar(
        chirp_interval_s,
        sim_defaults.get("chirp_interval_s"),
    )
    if resolved_chirp_interval is not None:
        backend_payload["chirp_interval_s"] = float(resolved_chirp_interval)

    map_cfg = _as_obj(asset_manifest, "map_config", required=False)
    out: Dict[str, Any] = {
        "scene_id": resolved_scene_id,
        "backend": backend_payload,
        "radar": radar_payload,
    }
    if len(map_cfg) > 0:
        out["map_config"] = map_cfg
    out["asset_bridge_metadata"] = {
        "source_type": "scene_asset_manifest",
        "object_count": int(len(objects)),
        "material_count": int(len(materials)),
    }
    return out


def _normalize_objects(raw_objects: Any, default_material_tag: str) -> list:
    if not isinstance(raw_objects, Sequence) or isinstance(raw_objects, (str, bytes)):
        raise ValueError("objects must be non-empty list")
    if len(raw_objects) == 0:
        raise ValueError("objects must be non-empty list")

    out = []
    for i, raw in enumerate(raw_objects):
        if not isinstance(raw, Mapping):
            raise ValueError(f"objects[{i}] must be object")
        obj_id = str(raw.get("object_id", raw.get("id", f"obj_{i:03d}")))
        centroid = raw.get("centroid_m", raw.get("bbox_center_m"))
        if not _is_vec3(centroid):
            raise ValueError(f"objects[{i}].centroid_m (or bbox_center_m) must be [x,y,z]")
        material_tag = str(raw.get("material_tag", raw.get("material", default_material_tag)))

        row: Dict[str, Any] = {
            "object_id": obj_id,
            "centroid_m": [float(x) for x in centroid],
            "material_tag": material_tag,
            "reflection_order": int(raw.get("reflection_order", 1)),
            "mesh_area_m2": float(raw.get("mesh_area_m2", raw.get("mesh_area", 1.0))),
            "rcs_scale": float(raw.get("rcs_scale", 1.0)),
            "amp": raw.get("amp", 1.0),
        }
        if "velocity_mps" in raw and _is_vec3(raw.get("velocity_mps")):
            row["velocity_mps"] = [float(x) for x in raw["velocity_mps"]]
        elif "radial_velocity_mps" in raw:
            row["radial_velocity_mps"] = float(raw["radial_velocity_mps"])

        if "path_id" in raw:
            row["path_id"] = str(raw["path_id"])
        if "source_mesh_uri" in raw:
            row["source_mesh_uri"] = str(raw["source_mesh_uri"])
        out.append(row)
    return out


def _normalize_materials(raw_materials: Any) -> Dict[str, Dict[str, float]]:
    if raw_materials is None:
        return {}

    if isinstance(raw_materials, Mapping):
        out: Dict[str, Dict[str, float]] = {}
        for key, value in raw_materials.items():
            tag = str(key)
            if not isinstance(value, Mapping):
                continue
            out[tag] = {
                "reflectivity": float(value.get("reflectivity", 1.0)),
                "attenuation_db": float(value.get("attenuation_db", 0.0)),
            }
        return out

    if isinstance(raw_materials, Sequence) and not isinstance(raw_materials, (str, bytes)):
        out = {}
        for i, row in enumerate(raw_materials):
            if not isinstance(row, Mapping):
                raise ValueError(f"materials[{i}] must be object")
            tag = str(row.get("material_tag", row.get("name", ""))).strip()
            if tag == "":
                raise ValueError(f"materials[{i}] missing material_tag")
            out[tag] = {
                "reflectivity": float(row.get("reflectivity", 1.0)),
                "attenuation_db": float(row.get("attenuation_db", 0.0)),
            }
        return out

    raise ValueError("materials must be object map or list")


def _is_pos_list(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return False
    if len(value) == 0:
        return False
    return all(_is_vec3(x) for x in value)


def _is_vec3(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return False
    if len(value) != 3:
        return False
    try:
        _ = [float(x) for x in value]
    except Exception:
        return False
    return True


def _as_obj(payload: Mapping[str, Any], key: str, required: bool = True) -> Dict[str, Any]:
    value = payload.get(key)
    if value is None and not required:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be object")
    return dict(value)


def _resolve_scalar(primary: Any, fallback: Any) -> Any:
    return fallback if primary is None else primary
