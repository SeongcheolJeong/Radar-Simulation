import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .adc_pack_builder import estimate_rd_ra_from_adc
from .constants import C0
from .io import save_adc_npz, save_paths_by_chirp_json
from .pipeline import run_hybrid_frames_pipeline
from .synth import synth_fmcw_tdm
from .types import Path as RadarPath
from .types import RadarConfig


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

    radar = _as_obj(scene_payload, "radar")
    map_cfg = _as_obj(scene_payload, "map_config", required=False)
    if backend_type == "hybrid_frames":
        result = _run_backend_hybrid_frames(
            backend=backend,
            radar=radar,
            output_dir=output_dir,
            run_hybrid_estimation=run_hybrid_estimation,
        )
    elif backend_type == "analytic_targets":
        result = _run_backend_analytic_targets(
            backend=backend,
            radar=radar,
            output_dir=output_dir,
        )
    else:
        raise ValueError(
            "supported backend.type: hybrid_frames, analytic_targets"
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
        "frame_count": int(result.get("frame_count", len(result["tx_schedule"]))),
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
        "frame_count": int(result.get("frame_count", len(result["tx_schedule"]))),
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


def _run_backend_hybrid_frames(
    backend: Mapping[str, Any],
    radar: Mapping[str, Any],
    output_dir: str,
    run_hybrid_estimation: bool,
) -> Dict[str, Any]:
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
    result["frame_count"] = int(len(frame_indices))
    return result


def _run_backend_analytic_targets(
    backend: Mapping[str, Any],
    radar: Mapping[str, Any],
    output_dir: str,
) -> Dict[str, Any]:
    tx_pos = _resolve_positions_3d(backend, "tx_pos_m")
    rx_pos = _resolve_positions_3d(backend, "rx_pos_m")
    n_tx = int(tx_pos.shape[0])

    n_chirps = _resolve_required_int(backend.get("n_chirps"), "backend.n_chirps")
    tx_schedule = _resolve_tx_schedule(
        raw=backend.get("tx_schedule"),
        n_chirps=n_chirps,
        n_tx=n_tx,
    )
    radar_cfg = RadarConfig(
        fc_hz=float(radar["fc_hz"]),
        slope_hz_per_s=float(radar["slope_hz_per_s"]),
        fs_hz=float(radar["fs_hz"]),
        samples_per_chirp=int(radar["samples_per_chirp"]),
        tx_schedule=tx_schedule,
    )
    chirp_interval_s = _opt_float(backend.get("chirp_interval_s"))
    if chirp_interval_s is None:
        chirp_interval_s = float(radar_cfg.samples_per_chirp) / float(radar_cfg.fs_hz)

    targets_raw = backend.get("targets")
    if not isinstance(targets_raw, Sequence) or isinstance(targets_raw, (str, bytes)):
        raise ValueError("backend.targets must be non-empty list")
    targets = [dict(_as_obj({"item": x}, "item")) for x in targets_raw]
    if len(targets) == 0:
        raise ValueError("backend.targets must be non-empty list")

    paths_by_chirp = _generate_analytic_paths(
        targets=targets,
        fc_hz=float(radar_cfg.fc_hz),
        n_chirps=n_chirps,
        chirp_interval_s=float(chirp_interval_s),
        min_range_m=max(float(backend.get("min_range_m", 0.1)), 1e-6),
    )

    adc = synth_fmcw_tdm(
        paths_by_chirp=paths_by_chirp,
        tx_pos_m=tx_pos,
        rx_pos_m=rx_pos,
        radar=radar_cfg,
        noise_sigma=float(backend.get("noise_sigma", 0.0)),
    )

    out_root = Path(output_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    path_json = out_root / "path_list.json"
    adc_npz = out_root / "adc_cube.npz"
    save_paths_by_chirp_json(paths_by_chirp, str(path_json))
    save_adc_npz(adc, radar_cfg, tx_pos, rx_pos, str(adc_npz))

    return {
        "paths_by_chirp": paths_by_chirp,
        "adc": adc,
        "tx_schedule": tx_schedule,
        "path_list_json": str(path_json),
        "adc_cube_npz": str(adc_npz),
        "hybrid_estimation_npz": None,
        "frame_count": int(n_chirps),
    }


def _generate_analytic_paths(
    targets: Sequence[Mapping[str, Any]],
    fc_hz: float,
    n_chirps: int,
    chirp_interval_s: float,
    min_range_m: float,
) -> List[List[RadarPath]]:
    lam = C0 / float(fc_hz)
    out: List[List[RadarPath]] = []
    for k in range(int(n_chirps)):
        t = float(k) * float(chirp_interval_s)
        chirp_paths: List[RadarPath] = []
        for target_idx, target in enumerate(targets):
            range0 = float(target["range_m"])
            velocity = float(target.get("radial_velocity_mps", 0.0))
            range_k = max(float(min_range_m), range0 + velocity * t)

            az_deg = float(target.get("az_deg", 0.0))
            el_deg = float(target.get("el_deg", 0.0))
            az = np.deg2rad(az_deg)
            el = np.deg2rad(el_deg)
            ux = float(np.cos(el) * np.cos(az))
            uy = float(np.cos(el) * np.sin(az))
            uz = float(np.sin(el))

            amp0 = _resolve_complex_scalar(target.get("amp", 1.0))
            range_amp_exp = float(target.get("range_amp_exponent", 2.0))
            amp = amp0 / (max(range_k, min_range_m) ** max(range_amp_exp, 0.0))
            path_id = str(
                target.get("path_id", f"analytic_t{int(target_idx):03d}_c{int(k):04d}")
            )
            material_tag = str(target.get("material_tag", "analytic_target"))
            reflection_order = int(target.get("reflection_order", 1))
            if reflection_order < 0:
                raise ValueError("target.reflection_order must be >= 0")

            chirp_paths.append(
                RadarPath(
                    delay_s=float(2.0 * range_k / C0),
                    doppler_hz=float(2.0 * velocity / lam),
                    unit_direction=(ux, uy, uz),
                    amp=complex(amp),
                    path_id=path_id,
                    material_tag=material_tag,
                    reflection_order=reflection_order,
                )
            )
        out.append(chirp_paths)
    return out


def _resolve_positions_3d(payload: Mapping[str, Any], key: str) -> np.ndarray:
    raw = payload.get(key)
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError(f"{key} must be list of [x,y,z]")
    arr = np.asarray(raw, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 3 or arr.shape[0] <= 0:
        raise ValueError(f"{key} must have shape (n,3)")
    return arr


def _resolve_tx_schedule(raw: Any, n_chirps: int, n_tx: int) -> List[int]:
    if raw is None:
        return [int(i % n_tx) for i in range(int(n_chirps))]
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("backend.tx_schedule must be list[int]")
    out = [int(x) for x in raw]
    if len(out) != int(n_chirps):
        raise ValueError("backend.tx_schedule length must equal n_chirps")
    for i, tx in enumerate(out):
        if tx < 0 or tx >= int(n_tx):
            raise ValueError(f"backend.tx_schedule[{i}] out of range: {tx}")
    return out


def _resolve_required_int(value: Any, key_name: str) -> int:
    if value is None:
        raise ValueError(f"{key_name} is required")
    out = int(value)
    if out <= 0:
        raise ValueError(f"{key_name} must be positive")
    return out


def _resolve_complex_scalar(value: Any) -> complex:
    if isinstance(value, Mapping):
        re = float(value.get("re", 0.0))
        im = float(value.get("im", 0.0))
        return complex(re, im)
    return complex(float(value), 0.0)


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
