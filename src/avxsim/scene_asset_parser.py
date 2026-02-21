import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence


DEFAULT_SIDECAR_PROFILE = "v1"
DEFAULT_SIDECAR_VERSION = 1


def load_scene_sidecar_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("scene sidecar json must be object")
    return payload


def save_asset_manifest_json(path: str, payload: Mapping[str, Any]) -> None:
    Path(path).write_text(json.dumps(dict(payload), indent=2), encoding="utf-8")


def build_asset_manifest_from_sidecar(
    sidecar_payload: Mapping[str, Any],
    sidecar_json_path: Optional[str] = None,
    mesh_root: Optional[str] = None,
    allow_missing_meshes: bool = False,
    default_material_tag: str = "default_material",
    profile: str = DEFAULT_SIDECAR_PROFILE,
    expected_sidecar_version: Optional[int] = DEFAULT_SIDECAR_VERSION,
    strict_mode: bool = True,
) -> Dict[str, Any]:
    unknown_keys = _collect_unknown_top_level_keys(sidecar_payload)
    if strict_mode and len(unknown_keys) > 0:
        raise ValueError(f"unknown top-level keys in strict mode: {sorted(unknown_keys)}")

    actual_profile = str(sidecar_payload.get("schema_profile", DEFAULT_SIDECAR_PROFILE))
    if str(profile) != actual_profile:
        raise ValueError(
            f"schema_profile mismatch: expected '{profile}', got '{actual_profile}'"
        )

    actual_version = int(sidecar_payload.get("schema_version", DEFAULT_SIDECAR_VERSION))
    if expected_sidecar_version is not None and int(expected_sidecar_version) != actual_version:
        raise ValueError(
            f"schema_version mismatch: expected {int(expected_sidecar_version)}, got {actual_version}"
        )

    scene_id = str(sidecar_payload.get("scene_id", "scene_from_sidecar"))
    sensor_mount = _as_obj(sidecar_payload, "sensor_mount")
    _validate_sensor_mount(sensor_mount)

    simulation_defaults = _as_obj(sidecar_payload, "simulation_defaults", required=False)
    radar = _as_obj(sidecar_payload, "radar", required=False)
    map_config = _as_obj(sidecar_payload, "map_config", required=False)
    materials = _normalize_materials(sidecar_payload.get("materials"))

    sidecar_dir = (
        None
        if sidecar_json_path is None
        else Path(sidecar_json_path).expanduser().resolve().parent
    )
    mesh_root_path = None if mesh_root is None else Path(mesh_root).expanduser().resolve()

    objects, parser_stats = _normalize_objects(
        raw_objects=sidecar_payload.get("objects"),
        sidecar_dir=sidecar_dir,
        mesh_root=mesh_root_path,
        allow_missing_meshes=bool(allow_missing_meshes),
        default_material_tag=str(default_material_tag),
        strict_mode=bool(strict_mode),
    )

    out: Dict[str, Any] = {
        "scene_id": scene_id,
        "sensor_mount": sensor_mount,
        "simulation_defaults": simulation_defaults,
        "radar": radar,
        "materials": materials,
        "objects": objects,
        "default_material_tag": str(default_material_tag),
        "asset_parser_metadata": {
            "source_type": "scene_sidecar",
            "object_count": int(len(objects)),
            "material_count": int(len(materials)),
            "mesh_format_counts": parser_stats["mesh_format_counts"],
            "allow_missing_meshes": bool(allow_missing_meshes),
            "strict_mode": bool(strict_mode),
            "schema_profile": actual_profile,
            "schema_version": int(actual_version),
            "unknown_top_level_keys": sorted(unknown_keys),
        },
    }
    if len(map_config) > 0:
        out["map_config"] = map_config
    return out


def _normalize_objects(
    raw_objects: Any,
    sidecar_dir: Optional[Path],
    mesh_root: Optional[Path],
    allow_missing_meshes: bool,
    default_material_tag: str,
    strict_mode: bool,
) -> tuple:
    if not isinstance(raw_objects, Sequence) or isinstance(raw_objects, (str, bytes)):
        raise ValueError("objects must be non-empty list")
    if len(raw_objects) == 0:
        raise ValueError("objects must be non-empty list")

    out = []
    format_counts = {"gltf": 0, "obj": 0}

    for i, raw in enumerate(raw_objects):
        if not isinstance(raw, Mapping):
            raise ValueError(f"objects[{i}] must be object")
        if strict_mode:
            unknown = _collect_unknown_object_keys(raw)
            if len(unknown) > 0:
                raise ValueError(
                    f"objects[{i}] has unknown keys in strict mode: {sorted(unknown)}"
                )
        mesh_uri = str(raw.get("mesh_uri", raw.get("mesh_file", raw.get("uri", "")))).strip()
        if mesh_uri == "":
            raise ValueError(f"objects[{i}] missing mesh_uri/mesh_file/uri")

        mesh_fmt = _resolve_mesh_format(mesh_uri)
        format_counts[mesh_fmt] += 1
        _validate_mesh_exists(
            mesh_uri=mesh_uri,
            sidecar_dir=sidecar_dir,
            mesh_root=mesh_root,
            allow_missing_meshes=allow_missing_meshes,
        )

        object_id = str(raw.get("object_id", raw.get("id", Path(mesh_uri).stem)))
        centroid = raw.get("centroid_m", raw.get("bbox_center_m"))
        if not _is_vec3(centroid):
            raise ValueError(f"objects[{i}].centroid_m (or bbox_center_m) must be [x,y,z]")

        material_tag = str(raw.get("material_tag", raw.get("material", default_material_tag)))
        row: Dict[str, Any] = {
            "object_id": object_id,
            "centroid_m": [float(x) for x in centroid],
            "material_tag": material_tag,
            "mesh_area_m2": float(raw.get("mesh_area_m2", raw.get("mesh_area", 1.0))),
            "rcs_scale": float(raw.get("rcs_scale", 1.0)),
            "reflection_order": int(raw.get("reflection_order", 1)),
            "amp": raw.get("amp", 1.0),
            "source_mesh_uri": mesh_uri,
            "source_mesh_format": mesh_fmt,
        }
        if "velocity_mps" in raw and _is_vec3(raw.get("velocity_mps")):
            row["velocity_mps"] = [float(x) for x in raw["velocity_mps"]]
        elif "radial_velocity_mps" in raw:
            row["radial_velocity_mps"] = float(raw["radial_velocity_mps"])
        if "path_id" in raw:
            row["path_id"] = str(raw["path_id"])
        out.append(row)

    return out, {"mesh_format_counts": format_counts}


def _validate_mesh_exists(
    mesh_uri: str,
    sidecar_dir: Optional[Path],
    mesh_root: Optional[Path],
    allow_missing_meshes: bool,
) -> None:
    if mesh_root is not None:
        p = (mesh_root / mesh_uri).resolve()
    elif sidecar_dir is not None:
        p = (sidecar_dir / mesh_uri).resolve()
    else:
        p = Path(mesh_uri).expanduser().resolve()
    if p.exists() and p.is_file():
        return
    if allow_missing_meshes:
        return
    raise FileNotFoundError(f"mesh file not found: {mesh_uri} (resolved: {p})")


def _resolve_mesh_format(mesh_uri: str) -> str:
    ext = Path(mesh_uri).suffix.lower()
    if ext in {".gltf", ".glb"}:
        return "gltf"
    if ext == ".obj":
        return "obj"
    raise ValueError(f"unsupported mesh extension for sidecar parser: {mesh_uri}")


def _normalize_materials(raw_materials: Any) -> Dict[str, Dict[str, float]]:
    if raw_materials is None:
        return {}

    if isinstance(raw_materials, Mapping):
        out: Dict[str, Dict[str, float]] = {}
        for key, value in raw_materials.items():
            if not isinstance(value, Mapping):
                continue
            out[str(key)] = {
                "reflectivity": float(value.get("reflectivity", 1.0)),
                "attenuation_db": float(value.get("attenuation_db", 0.0)),
            }
        return out

    if isinstance(raw_materials, Sequence) and not isinstance(raw_materials, (str, bytes)):
        out = {}
        for i, value in enumerate(raw_materials):
            if not isinstance(value, Mapping):
                raise ValueError(f"materials[{i}] must be object")
            tag = str(value.get("material_tag", value.get("name", ""))).strip()
            if tag == "":
                raise ValueError(f"materials[{i}] missing material_tag")
            out[tag] = {
                "reflectivity": float(value.get("reflectivity", 1.0)),
                "attenuation_db": float(value.get("attenuation_db", 0.0)),
            }
        return out

    raise ValueError("materials must be object map or list")


def _collect_unknown_top_level_keys(payload: Mapping[str, Any]) -> set:
    known = {
        "schema_profile",
        "schema_version",
        "scene_id",
        "sensor_mount",
        "simulation_defaults",
        "radar",
        "materials",
        "objects",
        "map_config",
    }
    return {str(k) for k in payload.keys() if str(k) not in known}


def _collect_unknown_object_keys(payload: Mapping[str, Any]) -> set:
    known = {
        "mesh_uri",
        "mesh_file",
        "uri",
        "object_id",
        "id",
        "centroid_m",
        "bbox_center_m",
        "material_tag",
        "material",
        "mesh_area_m2",
        "mesh_area",
        "rcs_scale",
        "reflection_order",
        "amp",
        "velocity_mps",
        "radial_velocity_mps",
        "path_id",
    }
    return {str(k) for k in payload.keys() if str(k) not in known}


def _validate_sensor_mount(sensor_mount: Mapping[str, Any]) -> None:
    tx = sensor_mount.get("tx_pos_m")
    rx = sensor_mount.get("rx_pos_m")
    if not _is_pos_list(tx):
        raise ValueError("sensor_mount.tx_pos_m must be list of [x,y,z]")
    if not _is_pos_list(rx):
        raise ValueError("sensor_mount.rx_pos_m must be list of [x,y,z]")
    ego = sensor_mount.get("ego_pos_m", [0.0, 0.0, 0.0])
    if not _is_vec3(ego):
        raise ValueError("sensor_mount.ego_pos_m must be [x,y,z]")


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
