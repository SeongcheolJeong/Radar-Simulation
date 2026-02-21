import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .adc_pack_builder import estimate_rd_ra_from_adc
from .pipeline import run_hybrid_frames_pipeline


def load_object_scene_json(scene_json_path: str) -> Dict[str, Any]:
    payload = json.loads(Path(scene_json_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("scene json must be object")
    return payload


def run_object_scene_to_radar_map(
    scene_payload: Mapping[str, Any],
    output_dir: str,
    run_hybrid_estimation: bool = False,
) -> Dict[str, Any]:
    backend = _as_obj(scene_payload, "backend")
    backend_type = str(backend.get("type", "")).strip().lower()
    if backend_type != "hybrid_frames":
        raise ValueError("currently supported backend.type: hybrid_frames")

    radar = _as_obj(scene_payload, "radar")
    map_cfg = _as_obj(scene_payload, "map_config", required=False)

    frame_indices = _resolve_frame_indices(backend)
    camera_rotate_deg = _resolve_float_pair(backend.get("camera_rotate_deg", [0.0, 0.0]))
    distance_limits_m = _resolve_float_pair(backend.get("distance_limits_m", [0.0, 100.0]))

    tx_ffd_files = _resolve_optional_path_list(backend.get("tx_ffd_files"))
    rx_ffd_files = _resolve_optional_path_list(backend.get("rx_ffd_files"))

    result = run_hybrid_frames_pipeline(
        frames_root_dir=str(backend["frames_root_dir"]),
        radar_json_path=str(backend["radar_json_path"]),
        frame_indices=frame_indices,
        fc_hz=float(radar["fc_hz"]),
        slope_hz_per_s=float(radar["slope_hz_per_s"]),
        fs_hz=float(radar["fs_hz"]),
        samples_per_chirp=int(radar["samples_per_chirp"]),
        camera_fov_deg=float(backend["camera_fov_deg"]),
        mode=str(backend.get("mode", "reflection")),
        file_ext=str(backend.get("file_ext", ".exr")),
        amplitude_prefix=str(backend.get("amplitude_prefix", "AmplitudeOutput")),
        distance_prefix=_opt_str(backend.get("distance_prefix")),
        distance_scale=_opt_float(backend.get("distance_scale")),
        camera_rotate_deg=camera_rotate_deg,
        amplitude_threshold=float(backend.get("amplitude_threshold", 0.0)),
        distance_limits_m=distance_limits_m,
        amplitude_scale=float(backend.get("amplitude_scale", 1.0)),
        top_k_per_chirp=_opt_int(backend.get("top_k_per_chirp")),
        path_power_fit_json=_opt_str(backend.get("path_power_fit_json")),
        path_power_apply_mode=str(backend.get("path_power_apply_mode", "shape_only")),
        tx_ffd_files=tx_ffd_files,
        rx_ffd_files=rx_ffd_files,
        ffd_field_format=str(backend.get("ffd_field_format", "auto")),
        use_jones_polarization=bool(backend.get("use_jones_polarization", False)),
        global_jones_matrix=_resolve_optional_jones(backend.get("global_jones_matrix")),
        run_hybrid_estimation=bool(run_hybrid_estimation),
        estimation_nfft=int(backend.get("estimation_nfft", 144)),
        estimation_range_bin_length=int(backend.get("estimation_range_bin_length", 10)),
        estimation_doppler_window=str(backend.get("estimation_doppler_window", "hann")),
        enable_motion_compensation=bool(backend.get("enable_motion_compensation", False)),
        motion_comp_fd_hz=_opt_float(backend.get("motion_comp_fd_hz")),
        motion_comp_chirp_interval_s=_opt_float(backend.get("motion_comp_chirp_interval_s")),
        motion_comp_reference_tx=_opt_int(backend.get("motion_comp_reference_tx")),
        output_dir=output_dir,
    )

    adc = np.asarray(result["adc"])
    est = estimate_rd_ra_from_adc(
        adc_sctr=adc,
        nfft_range=_opt_int(map_cfg.get("nfft_range") if map_cfg else None),
        nfft_doppler=_opt_int(map_cfg.get("nfft_doppler") if map_cfg else None),
        nfft_angle=_opt_int(map_cfg.get("nfft_angle") if map_cfg else None),
        range_window=str((map_cfg or {}).get("range_window", "hann")),
        doppler_window=str((map_cfg or {}).get("doppler_window", "hann")),
        angle_window=str((map_cfg or {}).get("angle_window", "hann")),
        range_bin_limit=_opt_int((map_cfg or {}).get("range_bin_limit")),
    )

    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    map_npz = out_root / "radar_map.npz"
    meta = {
        "scene_id": _opt_str(scene_payload.get("scene_id")),
        "backend_type": backend_type,
        "frame_count": int(len(frame_indices)),
        "tx_schedule": [int(x) for x in result["tx_schedule"]],
        "rd_ra_metadata": est["metadata"],
    }
    np.savez_compressed(
        str(map_npz),
        fx_dop_win=np.asarray(est["fx_dop_win"], dtype=np.float64),
        fx_ang=np.asarray(est["fx_ang"], dtype=np.float64),
        metadata_json=json.dumps(meta),
    )

    return {
        "path_list_json": str(out_root / "path_list.json"),
        "adc_cube_npz": str(out_root / "adc_cube.npz"),
        "radar_map_npz": str(map_npz),
        "tx_schedule": [int(x) for x in result["tx_schedule"]],
        "frame_count": int(len(frame_indices)),
        "hybrid_estimation_npz": result.get("hybrid_estimation_npz"),
    }


def run_object_scene_to_radar_map_json(
    scene_json_path: str,
    output_dir: str,
    run_hybrid_estimation: bool = False,
) -> Dict[str, Any]:
    payload = load_object_scene_json(scene_json_path)
    return run_object_scene_to_radar_map(
        scene_payload=payload,
        output_dir=output_dir,
        run_hybrid_estimation=run_hybrid_estimation,
    )


def _resolve_frame_indices(backend: Mapping[str, Any]) -> List[int]:
    raw = backend.get("frame_indices")
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        out = [int(x) for x in raw]
        if len(out) == 0:
            raise ValueError("backend.frame_indices must be non-empty")
        return out

    start = backend.get("frame_start")
    end = backend.get("frame_end")
    if start is None or end is None:
        raise ValueError("backend.frame_indices or backend.frame_start/frame_end required")
    s = int(start)
    e = int(end)
    if e < s:
        raise ValueError("backend.frame_end must be >= frame_start")
    return list(range(s, e + 1))


def _resolve_optional_jones(value: Any) -> Optional[np.ndarray]:
    if value is None:
        return None
    arr = np.asarray(value, dtype=np.complex128).reshape(-1)
    if arr.size != 4:
        raise ValueError("global_jones_matrix must provide 4 complex entries")
    return arr.reshape(2, 2)


def _resolve_optional_path_list(value: Any) -> Optional[Tuple[str, ...]]:
    if value is None:
        return None
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("expected list of file paths")
    out = tuple(str(x) for x in value)
    if len(out) == 0:
        return None
    return out


def _resolve_float_pair(value: Any) -> Tuple[float, float]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("expected pair of numeric values")
    if len(value) != 2:
        raise ValueError("expected exactly 2 values")
    return (float(value[0]), float(value[1]))


def _as_obj(payload: Mapping[str, Any], key: str, required: bool = True) -> Dict[str, Any]:
    value = payload.get(key)
    if value is None and not required:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be object")
    return dict(value)


def _opt_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return None if text == "" else text


def _opt_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def _opt_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    return int(value)
