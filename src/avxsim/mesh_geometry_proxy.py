import json
import struct
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


def infer_mesh_geometry_proxy(mesh_path: str, mesh_format: str) -> Dict[str, Any]:
    path = Path(mesh_path).expanduser().resolve()
    mesh_fmt = str(mesh_format).strip().lower()
    if mesh_fmt == "obj":
        return _infer_obj_geometry_proxy(path)
    if mesh_fmt == "gltf":
        return _infer_gltf_geometry_proxy(path)
    raise ValueError(f"unsupported mesh format for geometry proxy: {mesh_format}")


def _infer_obj_geometry_proxy(path: Path) -> Dict[str, Any]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    vertices: List[Tuple[float, float, float]] = []
    raw_faces: List[List[int]] = []
    for line in lines:
        s = line.strip()
        if s == "" or s.startswith("#"):
            continue
        if s.startswith("v "):
            parts = s.split()
            if len(parts) < 4:
                continue
            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
            continue
        if s.startswith("f "):
            parts = s.split()[1:]
            face: List[int] = []
            for token in parts:
                idx = _parse_obj_index(token)
                if idx is not None:
                    face.append(idx)
            if len(face) >= 3:
                raw_faces.append(face)

    if len(vertices) == 0:
        raise ValueError(f"obj proxy extraction failed: no vertices in {path}")

    min_v, max_v = _bbox_min_max(vertices)
    centroid = _bbox_center(min_v, max_v)

    area = 0.0
    for face in raw_faces:
        valid = _resolve_obj_face_indices(face, len(vertices))
        if len(valid) < 3:
            continue
        v0 = vertices[valid[0]]
        for i in range(1, len(valid) - 1):
            v1 = vertices[valid[i]]
            v2 = vertices[valid[i + 1]]
            area += _triangle_area(v0, v1, v2)
    if area <= 0.0:
        area = _bbox_surface_area(min_v, max_v)
    if area <= 0.0:
        area = 1.0

    return {
        "centroid_m": [float(x) for x in centroid],
        "mesh_area_m2": float(area),
        "proxy_source": "obj",
    }


def _infer_gltf_geometry_proxy(path: Path) -> Dict[str, Any]:
    ext = path.suffix.lower()
    if ext == ".gltf":
        payload = json.loads(path.read_text(encoding="utf-8"))
    elif ext == ".glb":
        payload = _load_glb_json(path)
    else:
        raise ValueError(f"gltf proxy extraction failed: unsupported extension {path.name}")

    min_v, max_v = _extract_gltf_position_bbox(payload)
    centroid = _bbox_center(min_v, max_v)
    area = _bbox_surface_area(min_v, max_v)
    if area <= 0.0:
        area = 1.0
    return {
        "centroid_m": [float(x) for x in centroid],
        "mesh_area_m2": float(area),
        "proxy_source": "gltf_metadata",
    }


def _load_glb_json(path: Path) -> Mapping[str, Any]:
    raw = path.read_bytes()
    if len(raw) < 20:
        raise ValueError(f"glb proxy extraction failed: invalid header size in {path}")
    if raw[0:4] != b"glTF":
        raise ValueError(f"glb proxy extraction failed: invalid magic in {path}")
    version = struct.unpack_from("<I", raw, 4)[0]
    if int(version) != 2:
        raise ValueError(f"glb proxy extraction failed: unsupported version {version} in {path}")

    offset = 12
    while offset + 8 <= len(raw):
        chunk_length = struct.unpack_from("<I", raw, offset)[0]
        chunk_type = struct.unpack_from("<I", raw, offset + 4)[0]
        chunk_start = offset + 8
        chunk_end = chunk_start + int(chunk_length)
        if chunk_end > len(raw):
            raise ValueError(f"glb proxy extraction failed: invalid chunk bounds in {path}")
        if chunk_type == 0x4E4F534A:
            text = raw[chunk_start:chunk_end].decode("utf-8", errors="ignore").rstrip("\x00")
            parsed = json.loads(text)
            if not isinstance(parsed, Mapping):
                raise ValueError(f"glb proxy extraction failed: JSON chunk is not object in {path}")
            return parsed
        offset = chunk_end

    raise ValueError(f"glb proxy extraction failed: JSON chunk not found in {path}")


def _extract_gltf_position_bbox(payload: Mapping[str, Any]) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    accessors = payload.get("accessors")
    meshes = payload.get("meshes")
    if not isinstance(accessors, Sequence) or isinstance(accessors, (str, bytes)):
        raise ValueError("gltf proxy extraction failed: accessors missing")
    if not isinstance(meshes, Sequence) or isinstance(meshes, (str, bytes)):
        raise ValueError("gltf proxy extraction failed: meshes missing")

    min_v: List[float] = [float("inf"), float("inf"), float("inf")]
    max_v: List[float] = [float("-inf"), float("-inf"), float("-inf")]
    found = False
    for mesh in meshes:
        if not isinstance(mesh, Mapping):
            continue
        primitives = mesh.get("primitives", [])
        if not isinstance(primitives, Sequence) or isinstance(primitives, (str, bytes)):
            continue
        for prim in primitives:
            if not isinstance(prim, Mapping):
                continue
            attrs = prim.get("attributes", {})
            if not isinstance(attrs, Mapping):
                continue
            pos_idx = attrs.get("POSITION")
            if not isinstance(pos_idx, int):
                continue
            if pos_idx < 0 or pos_idx >= len(accessors):
                continue
            accessor = accessors[pos_idx]
            if not isinstance(accessor, Mapping):
                continue
            a_min = accessor.get("min")
            a_max = accessor.get("max")
            if not _is_vec3_numeric(a_min) or not _is_vec3_numeric(a_max):
                continue
            for i in range(3):
                min_v[i] = min(min_v[i], float(a_min[i]))
                max_v[i] = max(max_v[i], float(a_max[i]))
            found = True

    if not found:
        raise ValueError("gltf proxy extraction failed: POSITION accessor min/max not found")
    return (min_v[0], min_v[1], min_v[2]), (max_v[0], max_v[1], max_v[2])


def _parse_obj_index(token: str) -> Optional[int]:
    if token == "":
        return None
    head = token.split("/")[0]
    if head == "":
        return None
    return int(head)


def _resolve_obj_face_indices(face: Sequence[int], vertex_count: int) -> List[int]:
    out: List[int] = []
    for item in face:
        idx = int(item)
        if idx > 0:
            resolved = idx - 1
        elif idx < 0:
            resolved = vertex_count + idx
        else:
            continue
        if resolved < 0 or resolved >= vertex_count:
            continue
        out.append(resolved)
    return out


def _triangle_area(
    a: Tuple[float, float, float],
    b: Tuple[float, float, float],
    c: Tuple[float, float, float],
) -> float:
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cx = ab[1] * ac[2] - ab[2] * ac[1]
    cy = ab[2] * ac[0] - ab[0] * ac[2]
    cz = ab[0] * ac[1] - ab[1] * ac[0]
    return 0.5 * (cx * cx + cy * cy + cz * cz) ** 0.5


def _bbox_min_max(
    vertices: Sequence[Tuple[float, float, float]]
) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    min_v = [float("inf"), float("inf"), float("inf")]
    max_v = [float("-inf"), float("-inf"), float("-inf")]
    for v in vertices:
        for i in range(3):
            min_v[i] = min(min_v[i], float(v[i]))
            max_v[i] = max(max_v[i], float(v[i]))
    return (min_v[0], min_v[1], min_v[2]), (max_v[0], max_v[1], max_v[2])


def _bbox_center(
    min_v: Tuple[float, float, float],
    max_v: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    return (
        0.5 * (float(min_v[0]) + float(max_v[0])),
        0.5 * (float(min_v[1]) + float(max_v[1])),
        0.5 * (float(min_v[2]) + float(max_v[2])),
    )


def _bbox_surface_area(
    min_v: Tuple[float, float, float],
    max_v: Tuple[float, float, float],
) -> float:
    dx = max(0.0, float(max_v[0]) - float(min_v[0]))
    dy = max(0.0, float(max_v[1]) - float(min_v[1]))
    dz = max(0.0, float(max_v[2]) - float(min_v[2]))
    area = 2.0 * (dx * dy + dy * dz + dz * dx)
    if area > 0.0:
        return area
    return max(dx * dy, dy * dz, dz * dx, 0.0)


def _is_vec3_numeric(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return False
    if len(value) != 3:
        return False
    try:
        _ = [float(x) for x in value]
    except Exception:
        return False
    return True
