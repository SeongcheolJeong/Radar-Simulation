import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Set, Tuple


DEFAULT_CARLA_EXPORT_PROFILE = "carla_export_v1"
DEFAULT_CARLA_EXPORT_VERSION = 1


def load_carla_export_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("carla export json must be object")
    return payload


def build_asset_manifest_from_carla_export(
    carla_payload: Mapping[str, Any],
    default_material_tag: str = "default_material",
    profile: str = DEFAULT_CARLA_EXPORT_PROFILE,
    expected_export_version: Optional[int] = DEFAULT_CARLA_EXPORT_VERSION,
    strict_mode: bool = True,
    include_ego_actor: bool = False,
    include_actor_types: Optional[Sequence[str]] = None,
    exclude_actor_types: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    unknown_keys = _collect_unknown_top_level_keys(carla_payload)
    if strict_mode and len(unknown_keys) > 0:
        raise ValueError(f"unknown top-level keys in strict mode: {sorted(unknown_keys)}")

    actual_profile = str(carla_payload.get("schema_profile", DEFAULT_CARLA_EXPORT_PROFILE))
    if str(profile) != actual_profile:
        raise ValueError(
            f"schema_profile mismatch: expected '{profile}', got '{actual_profile}'"
        )

    actual_version = int(carla_payload.get("schema_version", DEFAULT_CARLA_EXPORT_VERSION))
    if expected_export_version is not None and int(expected_export_version) != actual_version:
        raise ValueError(
            "schema_version mismatch: "
            f"expected {int(expected_export_version)}, got {actual_version}"
        )

    scene_id = str(carla_payload.get("scene_id", "scene_from_carla_export"))
    sensor_mount = _as_obj(carla_payload, "sensor_mount")
    _validate_sensor_mount(sensor_mount)

    simulation_defaults = _as_obj(carla_payload, "simulation_defaults", required=False)
    radar = _as_obj(carla_payload, "radar", required=False)
    map_config = _as_obj(carla_payload, "map_config", required=False)
    materials = _normalize_materials(carla_payload.get("materials"))

    actors_raw = carla_payload.get("actors")
    ego_actor_ids = _resolve_ego_actor_ids(carla_payload)
    objects, parser_stats = _normalize_actors(
        raw_actors=actors_raw,
        default_material_tag=str(default_material_tag),
        strict_mode=bool(strict_mode),
        include_ego_actor=bool(include_ego_actor),
        include_actor_types=include_actor_types,
        exclude_actor_types=exclude_actor_types,
        ego_actor_ids=ego_actor_ids,
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
            "source_type": "carla_export",
            "object_count": int(len(objects)),
            "material_count": int(len(materials)),
            "strict_mode": bool(strict_mode),
            "schema_profile": actual_profile,
            "schema_version": int(actual_version),
            "unknown_top_level_keys": sorted(unknown_keys),
            "unknown_actor_keys": parser_stats["unknown_actor_keys"],
            "actor_count": parser_stats["actor_count"],
            "excluded_actor_count": parser_stats["excluded_actor_count"],
            "excluded_ego_actor_count": parser_stats["excluded_ego_actor_count"],
            "excluded_sensor_actor_count": parser_stats["excluded_sensor_actor_count"],
            "excluded_filter_actor_count": parser_stats["excluded_filter_actor_count"],
            "include_ego_actor": bool(include_ego_actor),
            "include_actor_types": parser_stats["include_actor_types"],
            "exclude_actor_types": parser_stats["exclude_actor_types"],
            "auto_mesh_area_object_count": parser_stats["auto_mesh_area_object_count"],
            "auto_mesh_area_object_ids": parser_stats["auto_mesh_area_object_ids"],
            "dynamic_object_count": parser_stats["dynamic_object_count"],
            "static_object_count": parser_stats["static_object_count"],
            "actor_type_counts": parser_stats["actor_type_counts"],
        },
    }
    if len(map_config) > 0:
        out["map_config"] = map_config
    return out


def _normalize_actors(
    raw_actors: Any,
    default_material_tag: str,
    strict_mode: bool,
    include_ego_actor: bool,
    include_actor_types: Optional[Sequence[str]],
    exclude_actor_types: Optional[Sequence[str]],
    ego_actor_ids: Set[str],
) -> Tuple[list, Dict[str, Any]]:
    if not isinstance(raw_actors, Sequence) or isinstance(raw_actors, (str, bytes)):
        raise ValueError("actors must be non-empty list")
    if len(raw_actors) == 0:
        raise ValueError("actors must be non-empty list")

    include_set = _normalize_type_filter(include_actor_types)
    exclude_set = _normalize_type_filter(exclude_actor_types)
    unknown_actor_keys: Dict[str, Sequence[str]] = {}
    actor_type_counts: Dict[str, int] = {}
    auto_mesh_area_object_ids = []

    excluded_actor_count = 0
    excluded_ego_actor_count = 0
    excluded_sensor_actor_count = 0
    excluded_filter_actor_count = 0
    dynamic_object_count = 0
    static_object_count = 0

    out = []
    for i, raw in enumerate(raw_actors):
        if not isinstance(raw, Mapping):
            raise ValueError(f"actors[{i}] must be object")

        unknown = _collect_unknown_actor_keys(raw)
        if strict_mode and len(unknown) > 0:
            raise ValueError(f"actors[{i}] has unknown keys in strict mode: {sorted(unknown)}")
        if (not strict_mode) and len(unknown) > 0:
            actor_key = str(raw.get("actor_id", raw.get("id", i)))
            unknown_actor_keys[actor_key] = sorted(unknown)

        actor_id = str(raw.get("actor_id", raw.get("id", f"actor_{i:03d}"))).strip()
        actor_type = str(raw.get("actor_type", raw.get("type", "unknown"))).strip().lower()
        if actor_type == "":
            actor_type = "unknown"

        if _is_sensor_actor(actor_type):
            excluded_actor_count += 1
            excluded_sensor_actor_count += 1
            continue

        if (not include_ego_actor) and _is_ego_actor(raw=raw, actor_id=actor_id, ego_actor_ids=ego_actor_ids):
            excluded_actor_count += 1
            excluded_ego_actor_count += 1
            continue

        if (include_set is not None) and (actor_type not in include_set):
            excluded_actor_count += 1
            excluded_filter_actor_count += 1
            continue

        if (exclude_set is not None) and (actor_type in exclude_set):
            excluded_actor_count += 1
            excluded_filter_actor_count += 1
            continue

        centroid = _resolve_vec3(
            raw.get("centroid_m", raw.get("location_m", raw.get("position_m"))),
            f"actors[{i}].centroid/location",
        )
        material_tag = str(
            raw.get(
                "material_tag",
                raw.get("material", _infer_material_tag(actor_type, default_material_tag)),
            )
        )
        reflection_order = int(raw.get("reflection_order", 1))
        if reflection_order < 0:
            raise ValueError(f"actors[{i}].reflection_order must be >= 0")

        mesh_area_m2, used_auto_mesh_area = _resolve_mesh_area_m2(raw)
        if used_auto_mesh_area:
            auto_mesh_area_object_ids.append(actor_id)

        row: Dict[str, Any] = {
            "object_id": actor_id,
            "centroid_m": [float(x) for x in centroid],
            "material_tag": material_tag,
            "mesh_area_m2": float(mesh_area_m2),
            "rcs_scale": float(raw.get("rcs_scale", 1.0)),
            "reflection_order": int(reflection_order),
            "amp": raw.get("amp", 1.0),
            "source_carla_actor_id": actor_id,
            "source_carla_actor_type": actor_type,
        }

        velocity = _resolve_velocity_vector(raw)
        if velocity is not None:
            row["velocity_mps"] = [float(x) for x in velocity]
            dynamic_object_count += 1
        elif "radial_velocity_mps" in raw:
            row["radial_velocity_mps"] = float(raw.get("radial_velocity_mps", 0.0))
            if abs(float(row["radial_velocity_mps"])) > 0.0:
                dynamic_object_count += 1
            else:
                static_object_count += 1
        else:
            static_object_count += 1

        mesh_uri = str(raw.get("source_mesh_uri", raw.get("mesh_uri", ""))).strip()
        if mesh_uri != "":
            row["source_mesh_uri"] = mesh_uri
        if "path_id" in raw:
            row["path_id"] = str(raw["path_id"])
        out.append(row)

        actor_type_counts[actor_type] = int(actor_type_counts.get(actor_type, 0)) + 1

    if len(out) == 0:
        raise ValueError(
            "no usable actors after CARLA export filtering; check ego/filter configuration"
        )

    return out, {
        "unknown_actor_keys": unknown_actor_keys,
        "actor_count": int(len(raw_actors)),
        "excluded_actor_count": int(excluded_actor_count),
        "excluded_ego_actor_count": int(excluded_ego_actor_count),
        "excluded_sensor_actor_count": int(excluded_sensor_actor_count),
        "excluded_filter_actor_count": int(excluded_filter_actor_count),
        "include_actor_types": sorted(include_set) if include_set is not None else [],
        "exclude_actor_types": sorted(exclude_set) if exclude_set is not None else [],
        "auto_mesh_area_object_count": int(len(auto_mesh_area_object_ids)),
        "auto_mesh_area_object_ids": list(auto_mesh_area_object_ids),
        "dynamic_object_count": int(dynamic_object_count),
        "static_object_count": int(static_object_count),
        "actor_type_counts": dict(actor_type_counts),
    }


def _resolve_ego_actor_ids(payload: Mapping[str, Any]) -> Set[str]:
    out: Set[str] = set()
    for key in ("ego_actor_id", "ego_vehicle_id"):
        value = payload.get(key)
        if value is not None:
            out.add(str(value))
    ego_obj = payload.get("ego")
    if isinstance(ego_obj, Mapping):
        for key in ("actor_id", "id"):
            value = ego_obj.get(key)
            if value is not None:
                out.add(str(value))
    return out


def _is_ego_actor(raw: Mapping[str, Any], actor_id: str, ego_actor_ids: Set[str]) -> bool:
    if actor_id in ego_actor_ids:
        return True
    if bool(raw.get("is_ego", False)):
        return True
    role_name = str(raw.get("role_name", "")).strip().lower()
    if role_name in ("hero", "ego"):
        return True
    return False


def _is_sensor_actor(actor_type: str) -> bool:
    actor_type = str(actor_type).strip().lower()
    if actor_type == "":
        return False
    return actor_type.startswith("sensor.")


def _resolve_velocity_vector(raw: Mapping[str, Any]) -> Optional[Tuple[float, float, float]]:
    for key in ("velocity_mps", "velocity_world_mps", "velocity"):
        if key in raw:
            velocity = _resolve_vec3(raw.get(key), f"actor.{key}")
            return (float(velocity[0]), float(velocity[1]), float(velocity[2]))

    if ("speed_mps" in raw) and ("forward_m" in raw):
        speed = float(raw.get("speed_mps", 0.0))
        direction = _resolve_vec3(raw.get("forward_m"), "actor.forward_m")
        norm = (
            float(direction[0]) ** 2 + float(direction[1]) ** 2 + float(direction[2]) ** 2
        ) ** 0.5
        if norm > 0.0:
            return (
                float(speed * direction[0] / norm),
                float(speed * direction[1] / norm),
                float(speed * direction[2] / norm),
            )
    return None


def _resolve_mesh_area_m2(raw: Mapping[str, Any]) -> Tuple[float, bool]:
    if "mesh_area_m2" in raw:
        return max(float(raw.get("mesh_area_m2", 1.0)), 1e-6), False
    if "mesh_area" in raw:
        return max(float(raw.get("mesh_area", 1.0)), 1e-6), False

    bbox_half_extent = raw.get(
        "bbox_extent_m",
        raw.get("bbox_half_extent_m", raw.get("bbox_extents_m")),
    )
    if bbox_half_extent is not None:
        e = _resolve_vec3(bbox_half_extent, "actor.bbox_extent_m")
        ex = abs(float(e[0]))
        ey = abs(float(e[1]))
        ez = abs(float(e[2]))
        area = 8.0 * (ex * ey + ey * ez + ex * ez)
        return max(area, 1e-6), True

    bbox_size = raw.get("bbox_size_m")
    if bbox_size is not None:
        s = _resolve_vec3(bbox_size, "actor.bbox_size_m")
        lx = abs(float(s[0]))
        ly = abs(float(s[1]))
        lz = abs(float(s[2]))
        area = 2.0 * (lx * ly + ly * lz + lx * lz)
        return max(area, 1e-6), True

    return 1.0, True


def _normalize_type_filter(types: Optional[Sequence[str]]) -> Optional[Set[str]]:
    if types is None:
        return None
    out = {str(x).strip().lower() for x in types if str(x).strip() != ""}
    return out if len(out) > 0 else None


def _infer_material_tag(actor_type: str, default_material_tag: str) -> str:
    text = str(actor_type).strip().lower()
    if text.startswith("vehicle."):
        return "vehicle_metal"
    if text.startswith("walker."):
        return "pedestrian"
    if text.startswith("static."):
        return "static_object"
    if text.startswith("traffic."):
        return "traffic_device"
    return str(default_material_tag)


def _resolve_vec3(value: Any, key_name: str) -> Tuple[float, float, float]:
    if isinstance(value, Mapping):
        keys = ("x", "y", "z")
        if all(k in value for k in keys):
            return (float(value["x"]), float(value["y"]), float(value["z"]))
        raise ValueError(f"{key_name} dict must contain x/y/z")

    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{key_name} must be [x,y,z] or {{x,y,z}}")
    if len(value) != 3:
        raise ValueError(f"{key_name} must have length 3")
    return (float(value[0]), float(value[1]), float(value[2]))


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


def _collect_unknown_top_level_keys(payload: Mapping[str, Any]) -> Set[str]:
    known = {
        "schema_profile",
        "schema_version",
        "scene_id",
        "sensor_mount",
        "simulation_defaults",
        "radar",
        "materials",
        "actors",
        "map_config",
        "frame_id",
        "timestamp_s",
        "carla_metadata",
        "metadata",
        "ego_actor_id",
        "ego_vehicle_id",
        "ego",
    }
    return {str(k) for k in payload.keys() if str(k) not in known}


def _collect_unknown_actor_keys(payload: Mapping[str, Any]) -> Set[str]:
    known = {
        "actor_id",
        "id",
        "actor_type",
        "type",
        "role_name",
        "is_ego",
        "centroid_m",
        "location_m",
        "position_m",
        "velocity_mps",
        "velocity_world_mps",
        "velocity",
        "speed_mps",
        "forward_m",
        "radial_velocity_mps",
        "material_tag",
        "material",
        "mesh_area_m2",
        "mesh_area",
        "bbox_extent_m",
        "bbox_half_extent_m",
        "bbox_extents_m",
        "bbox_size_m",
        "rcs_scale",
        "reflection_order",
        "amp",
        "source_mesh_uri",
        "mesh_uri",
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
    _ = _resolve_vec3(ego, "sensor_mount.ego_pos_m")


def _is_pos_list(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return False
    if len(value) == 0:
        return False
    try:
        for item in value:
            _ = _resolve_vec3(item, "sensor_mount")
        return True
    except Exception:
        return False


def _as_obj(payload: Mapping[str, Any], key: str, required: bool = True) -> Dict[str, Any]:
    value = payload.get(key)
    if value is None and not required:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be object")
    return dict(value)
