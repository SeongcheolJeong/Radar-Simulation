import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .adapters import (
    adapt_po_sbr_paths_payload_to_paths_by_chirp,
    adapt_radarsimpy_paths_payload_to_paths_by_chirp,
    adapt_sionna_paths_payload_to_paths_by_chirp,
    load_po_sbr_paths_json,
    load_radarsimpy_paths_json,
    load_sionna_paths_json,
)
from .adc_pack_builder import estimate_rd_ra_from_adc
from .antenna import FfdAntennaModel
from .constants import C0
from .io import save_adc_npz, save_paths_by_chirp_json
from .lgit_output_adapter import save_lgit_customized_output_npz
from .path_contract import validate_paths_by_chirp
from .pipeline import run_hybrid_frames_pipeline
from .radar_compensation import apply_radar_compensation
from .runtime_coupling import invoke_runtime_paths_provider
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
    elif backend_type == "mesh_material_stub":
        result = _run_backend_mesh_material_stub(
            backend=backend,
            radar=radar,
            output_dir=output_dir,
        )
    elif backend_type == "sionna_rt":
        result = _run_backend_sionna_rt(
            backend=backend,
            radar=radar,
            output_dir=output_dir,
        )
    elif backend_type == "po_sbr_rt":
        result = _run_backend_po_sbr_rt(
            backend=backend,
            radar=radar,
            output_dir=output_dir,
        )
    elif backend_type == "radarsimpy_rt":
        result = _run_backend_radarsimpy_rt(
            backend=backend,
            radar=radar,
            output_dir=output_dir,
        )
    else:
        raise ValueError(
            "supported backend.type: hybrid_frames, analytic_targets, mesh_material_stub, "
            "sionna_rt, po_sbr_rt, radarsimpy_rt"
        )

    if "paths_by_chirp" not in result:
        raise ValueError("backend result missing paths_by_chirp")
    path_contract_summary = validate_paths_by_chirp(
        paths_by_chirp=result["paths_by_chirp"],
        n_chirps=len(result["tx_schedule"]),
        require_metadata=True,
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
    if "runtime_resolution" in result:
        meta["runtime_resolution"] = result["runtime_resolution"]
    if "antenna_summary" in result and isinstance(result["antenna_summary"], Mapping):
        meta["antenna_summary"] = dict(result["antenna_summary"])
    if "compensation_summary" in result and isinstance(result["compensation_summary"], Mapping):
        meta["compensation_summary"] = dict(result["compensation_summary"])
    meta["path_contract_summary"] = dict(path_contract_summary)

    lgit_output_npz: Optional[str] = None
    lgit_cfg = _resolve_lgit_output_adapter_config(scene_payload)
    if bool(lgit_cfg.get("enabled", False)):
        lgit_path = (out_root / str(lgit_cfg["filename"])).resolve()
        lgit_meta = {
            "scene_id": _opt_str(scene_payload.get("scene_id")),
            "backend_type": backend_type,
            "frame_count": int(result.get("frame_count", len(result["tx_schedule"]))),
        }
        lgit_summary = save_lgit_customized_output_npz(
            output_npz=lgit_path,
            adc_sctr=adc,
            tx_schedule=[int(x) for x in result["tx_schedule"]],
            multiplexing_mode=_resolve_result_multiplexing_mode(result),
            metadata=lgit_meta,
        )
        lgit_output_npz = str(lgit_path)
        meta["lgit_customized_output_npz"] = str(lgit_output_npz)
        meta["lgit_customized_output_summary"] = dict(lgit_summary)

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
        "lgit_customized_output_npz": lgit_output_npz,
        "path_contract_summary": dict(path_contract_summary),
    }


def run_object_scene_to_radar_map_json(
    scene_json_path: str,
    output_dir: str,
    run_hybrid_estimation: bool = False,
) -> Dict[str, Any]:
    payload = load_object_scene_json(scene_json_path)
    payload = _resolve_scene_relative_paths(
        payload=payload,
        scene_json_path=scene_json_path,
    )
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


def _resolve_lgit_output_adapter_config(scene_payload: Mapping[str, Any]) -> Dict[str, Any]:
    defaults: Dict[str, Any] = {
        "enabled": True,
        "filename": "lgit_customized_output.npz",
    }
    output_adapters = scene_payload.get("output_adapters")
    if not isinstance(output_adapters, Mapping):
        return defaults

    raw = output_adapters.get("lgit_customized")
    if raw is None:
        return defaults
    if isinstance(raw, bool):
        out = dict(defaults)
        out["enabled"] = bool(raw)
        return out
    if not isinstance(raw, Mapping):
        raise ValueError("output_adapters.lgit_customized must be bool or object")

    out = dict(defaults)
    out["enabled"] = bool(raw.get("enabled", True))
    filename = _opt_str(raw.get("filename"))
    if filename is not None:
        text = str(filename).strip()
        if text == "":
            raise ValueError("output_adapters.lgit_customized.filename must be non-empty when set")
        if ("/" in text) or ("\\" in text):
            raise ValueError("output_adapters.lgit_customized.filename must be a filename only")
        out["filename"] = str(text)
    return out


def _resolve_result_multiplexing_mode(result: Mapping[str, Any]) -> str:
    runtime_resolution = result.get("runtime_resolution")
    if not isinstance(runtime_resolution, Mapping):
        return "tdm"
    provider_info = runtime_resolution.get("provider_runtime_info")
    if not isinstance(provider_info, Mapping):
        return "tdm"
    mode = _opt_str(provider_info.get("multiplexing_mode"))
    if mode is None:
        return "tdm"
    return str(mode)


def _resolve_scene_relative_paths(payload: Mapping[str, Any], scene_json_path: str) -> Dict[str, Any]:
    out = json.loads(json.dumps(dict(payload)))
    backend = out.get("backend")
    if not isinstance(backend, dict):
        return out
    radar_comp = backend.get("radar_compensation")
    if not isinstance(radar_comp, dict):
        return out
    manifold = radar_comp.get("manifold")
    if not isinstance(manifold, dict):
        return out

    raw_path = manifold.get("asset_path", manifold.get("asset_npz", manifold.get("asset_h5")))
    if raw_path is None:
        return out
    text = str(raw_path).strip()
    if text == "":
        manifold.pop("asset_path", None)
        manifold.pop("asset_npz", None)
        manifold.pop("asset_h5", None)
        return out
    p = Path(text).expanduser()
    if p.is_absolute():
        manifold["asset_path"] = str(p.resolve())
        manifold.pop("asset_npz", None)
        manifold.pop("asset_h5", None)
        return out
    scene_dir = Path(scene_json_path).expanduser().resolve().parent
    manifold["asset_path"] = str((scene_dir / p).resolve())
    manifold.pop("asset_npz", None)
    manifold.pop("asset_h5", None)
    return out


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
    paths_by_chirp, compensation_summary = _apply_optional_radar_compensation(
        paths_by_chirp=paths_by_chirp,
        backend=backend,
        radar_cfg=radar_cfg,
        chirp_interval_s=float(chirp_interval_s),
    )

    adc, antenna_summary = _synth_backend_adc(
        backend=backend,
        paths_by_chirp=paths_by_chirp,
        tx_pos=tx_pos,
        rx_pos=rx_pos,
        radar_cfg=radar_cfg,
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
        "antenna_summary": antenna_summary,
        "compensation_summary": compensation_summary,
    }


def _run_backend_mesh_material_stub(
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
    ego_pos = _resolve_vector3(backend.get("ego_pos_m", [0.0, 0.0, 0.0]), "backend.ego_pos_m")
    min_range_m = max(float(backend.get("min_range_m", 0.1)), 1e-6)
    default_material_tag = str(backend.get("default_material_tag", "default_material"))

    objects_raw = backend.get("objects")
    if not isinstance(objects_raw, Sequence) or isinstance(objects_raw, (str, bytes)):
        raise ValueError("backend.objects must be non-empty list")
    objects = [dict(_as_obj({"item": x}, "item")) for x in objects_raw]
    if len(objects) == 0:
        raise ValueError("backend.objects must be non-empty list")

    materials = _as_obj(backend, "materials", required=False)
    range_amp_exp = max(float(backend.get("range_amp_exponent", 2.0)), 0.0)

    paths_by_chirp = _generate_mesh_material_paths(
        objects=objects,
        materials=materials,
        default_material_tag=default_material_tag,
        fc_hz=float(radar_cfg.fc_hz),
        n_chirps=n_chirps,
        chirp_interval_s=float(chirp_interval_s),
        min_range_m=float(min_range_m),
        range_amp_exp=float(range_amp_exp),
        ego_pos_m=ego_pos,
    )
    paths_by_chirp, compensation_summary = _apply_optional_radar_compensation(
        paths_by_chirp=paths_by_chirp,
        backend=backend,
        radar_cfg=radar_cfg,
        chirp_interval_s=float(chirp_interval_s),
    )

    adc, antenna_summary = _synth_backend_adc(
        backend=backend,
        paths_by_chirp=paths_by_chirp,
        tx_pos=tx_pos,
        rx_pos=rx_pos,
        radar_cfg=radar_cfg,
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
        "antenna_summary": antenna_summary,
        "compensation_summary": compensation_summary,
    }


def _run_backend_sionna_rt(
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
    static_payload = _resolve_optional_static_paths_payload(
        backend=backend,
        backend_type="sionna_rt",
        paths_json_key="sionna_paths_json",
        json_loader=load_sionna_paths_json,
    )
    paths_payload, runtime_resolution = _resolve_paths_payload_with_runtime(
        backend=backend,
        radar=radar,
        backend_type="sionna_rt",
        n_chirps=int(n_chirps),
        fc_hz=float(radar_cfg.fc_hz),
        static_payload=static_payload,
        static_requirement_label="paths_payload, sionna_paths_json",
        default_runtime_required_modules=("sionna", "tensorflow"),
    )

    paths_by_chirp = adapt_sionna_paths_payload_to_paths_by_chirp(
        payload=paths_payload,
        n_chirps=int(n_chirps),
    )
    chirp_interval_s = _resolve_backend_chirp_interval_s(backend=backend, radar_cfg=radar_cfg)
    paths_by_chirp, compensation_summary = _apply_optional_radar_compensation(
        paths_by_chirp=paths_by_chirp,
        backend=backend,
        radar_cfg=radar_cfg,
        chirp_interval_s=float(chirp_interval_s),
    )

    adc, antenna_summary = _synth_backend_adc(
        backend=backend,
        paths_by_chirp=paths_by_chirp,
        tx_pos=tx_pos,
        rx_pos=rx_pos,
        radar_cfg=radar_cfg,
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
        "runtime_resolution": runtime_resolution,
        "antenna_summary": antenna_summary,
        "compensation_summary": compensation_summary,
    }


def _run_backend_po_sbr_rt(
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
    static_payload = _resolve_optional_static_paths_payload(
        backend=backend,
        backend_type="po_sbr_rt",
        paths_json_key="po_sbr_paths_json",
        json_loader=load_po_sbr_paths_json,
    )
    paths_payload, runtime_resolution = _resolve_paths_payload_with_runtime(
        backend=backend,
        radar=radar,
        backend_type="po_sbr_rt",
        n_chirps=int(n_chirps),
        fc_hz=float(radar_cfg.fc_hz),
        static_payload=static_payload,
        static_requirement_label="paths_payload, po_sbr_paths_json",
        default_runtime_required_modules=(),
    )

    paths_by_chirp = adapt_po_sbr_paths_payload_to_paths_by_chirp(
        payload=paths_payload,
        n_chirps=int(n_chirps),
        fc_hz=float(radar_cfg.fc_hz),
    )
    chirp_interval_s = _resolve_backend_chirp_interval_s(backend=backend, radar_cfg=radar_cfg)
    paths_by_chirp, compensation_summary = _apply_optional_radar_compensation(
        paths_by_chirp=paths_by_chirp,
        backend=backend,
        radar_cfg=radar_cfg,
        chirp_interval_s=float(chirp_interval_s),
    )

    adc, antenna_summary = _synth_backend_adc(
        backend=backend,
        paths_by_chirp=paths_by_chirp,
        tx_pos=tx_pos,
        rx_pos=rx_pos,
        radar_cfg=radar_cfg,
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
        "runtime_resolution": runtime_resolution,
        "antenna_summary": antenna_summary,
        "compensation_summary": compensation_summary,
    }


def _run_backend_radarsimpy_rt(
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
    static_payload = _resolve_optional_static_paths_payload(
        backend=backend,
        backend_type="radarsimpy_rt",
        paths_json_key="radarsimpy_paths_json",
        json_loader=load_radarsimpy_paths_json,
    )
    backend_runtime = dict(backend)
    backend_runtime["resolved_tx_schedule"] = [int(x) for x in tx_schedule]
    payload, runtime_resolution = _resolve_paths_payload_with_runtime(
        backend=backend_runtime,
        radar=radar,
        backend_type="radarsimpy_rt",
        n_chirps=int(n_chirps),
        fc_hz=float(radar_cfg.fc_hz),
        static_payload=static_payload,
        static_requirement_label="paths_payload, radarsimpy_paths_json",
        default_runtime_required_modules=("radarsimpy",),
    )
    paths_by_chirp = adapt_radarsimpy_paths_payload_to_paths_by_chirp(
        payload=payload,
        n_chirps=int(n_chirps),
        fc_hz=float(radar_cfg.fc_hz),
    )
    chirp_interval_s = _resolve_backend_chirp_interval_s(backend=backend, radar_cfg=radar_cfg)
    paths_by_chirp, compensation_summary = _apply_optional_radar_compensation(
        paths_by_chirp=paths_by_chirp,
        backend=backend,
        radar_cfg=radar_cfg,
        chirp_interval_s=float(chirp_interval_s),
    )
    adc_payload = _resolve_optional_adc_sctr_from_payload(
        payload=payload,
        samples_per_chirp=int(radar_cfg.samples_per_chirp),
        n_chirps=int(n_chirps),
        n_tx=int(tx_pos.shape[0]),
        n_rx=int(rx_pos.shape[0]),
    )
    synth_options, antenna_summary = _resolve_backend_synth_options(
        backend=backend,
        n_tx=int(tx_pos.shape[0]),
        n_rx=int(rx_pos.shape[0]),
    )
    compensation_enabled = bool(compensation_summary.get("enabled", False))
    synth_requires_path = bool(antenna_summary.get("synth_requires_path", False))
    adc_source = "synth_fmcw_tdm"
    if (adc_payload is not None) and (not compensation_enabled) and (not synth_requires_path):
        adc = np.asarray(adc_payload)
        adc_source = "runtime_payload_adc_sctr"
    else:
        adc = synth_fmcw_tdm(
            paths_by_chirp=paths_by_chirp,
            tx_pos_m=tx_pos,
            rx_pos_m=rx_pos,
            radar=radar_cfg,
            noise_sigma=float(backend.get("noise_sigma", 0.0)),
            **synth_options,
        )
        if adc_payload is not None:
            compensation_summary = dict(compensation_summary)
            compensation_summary["adc_payload_ignored"] = True
            if compensation_enabled and synth_requires_path:
                compensation_summary["adc_payload_ignored_reason"] = (
                    "radar_compensation_enabled_and_antenna_path_synth_required"
                )
            elif compensation_enabled:
                compensation_summary["adc_payload_ignored_reason"] = "radar_compensation_enabled"
            elif synth_requires_path:
                compensation_summary["adc_payload_ignored_reason"] = "antenna_path_synth_required"
            else:
                compensation_summary["adc_payload_ignored_reason"] = "path_synth_selected"

    runtime_resolution_out = dict(runtime_resolution)
    runtime_resolution_out["adc_source"] = str(adc_source)
    runtime_resolution_out["adc_payload_present"] = bool(adc_payload is not None)
    provider_runtime_info = payload.get("provider_runtime_info")
    if isinstance(provider_runtime_info, Mapping):
        runtime_resolution_out["provider_runtime_info"] = dict(provider_runtime_info)

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
        "runtime_resolution": runtime_resolution_out,
        "antenna_summary": antenna_summary,
        "compensation_summary": compensation_summary,
    }


def _resolve_optional_adc_sctr_from_payload(
    payload: Mapping[str, Any],
    samples_per_chirp: int,
    n_chirps: int,
    n_tx: int,
    n_rx: int,
) -> Optional[np.ndarray]:
    raw = payload.get("adc_sctr")
    if raw is None:
        return None
    arr = np.asarray(raw)
    if arr.ndim != 4:
        raise ValueError("backend payload adc_sctr must be 4D [sample,chirp,tx,rx]")
    expected = (int(samples_per_chirp), int(n_chirps), int(n_tx), int(n_rx))
    if tuple(int(x) for x in arr.shape) != expected:
        raise ValueError(f"backend payload adc_sctr shape mismatch: {tuple(arr.shape)} != {expected}")
    arr_c = np.asarray(arr, dtype=np.complex128)
    if (not np.all(np.isfinite(np.real(arr_c)))) or (not np.all(np.isfinite(np.imag(arr_c)))):
        raise ValueError("backend payload adc_sctr contains non-finite values")
    return arr_c


def _resolve_backend_synth_options(
    backend: Mapping[str, Any],
    *,
    n_tx: int,
    n_rx: int,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    tx_ffd_files = _resolve_optional_path_list(backend.get("tx_ffd_files"))
    rx_ffd_files = _resolve_optional_path_list(backend.get("rx_ffd_files"))
    if (tx_ffd_files is None) != (rx_ffd_files is None):
        raise ValueError("backend.tx_ffd_files and backend.rx_ffd_files must be provided together")

    use_jones_polarization = bool(backend.get("use_jones_polarization", False))
    global_jones_matrix = _resolve_optional_jones(backend.get("global_jones_matrix"))
    synth_options: Dict[str, Any] = {
        "use_jones_polarization": bool(use_jones_polarization),
        "global_jones_matrix": global_jones_matrix,
    }
    antenna_mode = "isotropic"
    if tx_ffd_files is not None:
        synth_options["antenna_model"] = FfdAntennaModel.from_files(
            tx_ffd_files=tx_ffd_files,
            rx_ffd_files=rx_ffd_files,
            n_tx=int(n_tx),
            n_rx=int(n_rx),
            field_format=str(backend.get("ffd_field_format", "auto")),
        )
        antenna_mode = "ffd_jones" if use_jones_polarization else "ffd"
    elif use_jones_polarization or (global_jones_matrix is not None):
        antenna_mode = "jones"

    antenna_summary = {
        "antenna_mode": antenna_mode,
        "ffd_enabled": bool(tx_ffd_files is not None),
        "use_jones_polarization": bool(use_jones_polarization),
        "global_jones_enabled": bool(global_jones_matrix is not None),
        "tx_ffd_file_count": int(len(tx_ffd_files) if tx_ffd_files is not None else 0),
        "rx_ffd_file_count": int(len(rx_ffd_files) if rx_ffd_files is not None else 0),
        "synth_requires_path": bool(
            (tx_ffd_files is not None) or use_jones_polarization or (global_jones_matrix is not None)
        ),
    }
    return synth_options, antenna_summary


def _synth_backend_adc(
    *,
    backend: Mapping[str, Any],
    paths_by_chirp: Sequence[Sequence[RadarPath]],
    tx_pos: np.ndarray,
    rx_pos: np.ndarray,
    radar_cfg: RadarConfig,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    synth_options, antenna_summary = _resolve_backend_synth_options(
        backend=backend,
        n_tx=int(tx_pos.shape[0]),
        n_rx=int(rx_pos.shape[0]),
    )
    adc = synth_fmcw_tdm(
        paths_by_chirp=paths_by_chirp,
        tx_pos_m=tx_pos,
        rx_pos_m=rx_pos,
        radar=radar_cfg,
        noise_sigma=float(backend.get("noise_sigma", 0.0)),
        **synth_options,
    )
    return adc, antenna_summary


def _resolve_optional_static_paths_payload(
    backend: Mapping[str, Any],
    backend_type: str,
    paths_json_key: str,
    json_loader: Any,
) -> Optional[Dict[str, Any]]:
    raw_paths_payload = backend.get("paths_payload")
    paths_json = _opt_str(backend.get(paths_json_key))
    if (raw_paths_payload is not None) and (paths_json is not None):
        raise ValueError(
            f"{backend_type} backend allows only one of: paths_payload, {paths_json_key}"
        )
    if paths_json is not None:
        payload = json_loader(paths_json)
        if not isinstance(payload, Mapping):
            raise ValueError(f"{paths_json_key} must resolve to object payload")
        return dict(payload)
    if raw_paths_payload is not None:
        if not isinstance(raw_paths_payload, Mapping):
            raise ValueError("backend.paths_payload must be object when provided")
        return dict(raw_paths_payload)
    return None


def _resolve_paths_payload_with_runtime(
    backend: Mapping[str, Any],
    radar: Mapping[str, Any],
    backend_type: str,
    n_chirps: int,
    fc_hz: float,
    static_payload: Optional[Mapping[str, Any]],
    static_requirement_label: str,
    default_runtime_required_modules: Sequence[str],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    runtime_provider = _opt_str(backend.get("runtime_provider"))
    if runtime_provider is None:
        if static_payload is None:
            raise ValueError(
                f"{backend_type} backend requires one of: {static_requirement_label}, runtime_provider"
            )
        return (
            dict(static_payload),
            {
                "mode": "static_only",
                "backend_type": backend_type,
                "runtime_provider": None,
            },
        )

    runtime_required_modules = _resolve_optional_string_list(
        backend.get("runtime_required_modules"),
        key_name="backend.runtime_required_modules",
    )
    if runtime_required_modules is None:
        runtime_required_modules = tuple(str(x) for x in default_runtime_required_modules)
    runtime_input = _as_obj(backend, "runtime_input", required=False)
    runtime_context = {
        "backend_type": backend_type,
        "n_chirps": int(n_chirps),
        "fc_hz": float(fc_hz),
        "radar": dict(radar),
        "backend": dict(backend),
        "runtime_input": runtime_input,
    }
    try:
        payload, runtime_info = invoke_runtime_paths_provider(
            provider_spec=runtime_provider,
            context=runtime_context,
            required_modules=runtime_required_modules,
        )
        return (
            dict(payload),
            {
                "mode": "runtime_provider",
                "backend_type": backend_type,
                "runtime_provider": runtime_provider,
                "runtime_info": runtime_info,
            },
        )
    except Exception as exc:
        runtime_policy = str(backend.get("runtime_failure_policy", "error")).strip().lower()
        if runtime_policy not in ("error", "use_static"):
            raise ValueError("runtime_failure_policy must be one of: error, use_static")
        if (runtime_policy == "use_static") and (static_payload is not None):
            return (
                dict(static_payload),
                {
                    "mode": "runtime_failed_fallback_static",
                    "backend_type": backend_type,
                    "runtime_provider": runtime_provider,
                    "runtime_error": f"{type(exc).__name__}: {exc}",
                },
            )
        raise ValueError(f"{backend_type} runtime provider failed: {exc}") from exc


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


def _generate_mesh_material_paths(
    objects: Sequence[Mapping[str, Any]],
    materials: Mapping[str, Any],
    default_material_tag: str,
    fc_hz: float,
    n_chirps: int,
    chirp_interval_s: float,
    min_range_m: float,
    range_amp_exp: float,
    ego_pos_m: np.ndarray,
) -> List[List[RadarPath]]:
    lam = C0 / float(fc_hz)
    out: List[List[RadarPath]] = []
    for k in range(int(n_chirps)):
        t = float(k) * float(chirp_interval_s)
        chirp_paths: List[RadarPath] = []
        for obj_idx, obj in enumerate(objects):
            obj_id = str(obj.get("object_id", f"obj_{int(obj_idx):03d}"))
            material_tag = str(obj.get("material_tag", default_material_tag))
            mat = materials.get(material_tag, {})
            if not isinstance(mat, Mapping):
                mat = {}

            pos0 = _resolve_vector3(obj.get("centroid_m"), f"object[{obj_idx}].centroid_m")
            vel = _resolve_velocity_vector(obj, obj_idx, ego_pos_m=ego_pos_m, pos0=pos0)
            pos_t = pos0 + vel * t
            rel = pos_t - ego_pos_m
            rng = float(np.linalg.norm(rel))
            if not np.isfinite(rng) or rng <= float(min_range_m):
                continue
            u = rel / rng

            radial_v = float(np.dot(vel, u))
            amp0 = _resolve_complex_scalar(obj.get("amp", 1.0))
            rcs_scale = max(float(obj.get("rcs_scale", 1.0)), 0.0)
            mesh_area = max(float(obj.get("mesh_area_m2", 1.0)), 0.0)
            reflectivity = max(float(mat.get("reflectivity", 1.0)), 0.0)
            attenuation_db = float(mat.get("attenuation_db", 0.0))
            attenuation_lin = 10.0 ** (-attenuation_db / 20.0)
            reflection_order = int(obj.get("reflection_order", 1))
            if reflection_order < 0:
                raise ValueError(f"object[{obj_idx}].reflection_order must be >= 0")

            order_gain = reflectivity ** max(reflection_order - 1, 0)
            amp_scale = (
                attenuation_lin
                * np.sqrt(max(reflectivity, 0.0))
                * np.sqrt(max(rcs_scale, 0.0))
                * np.sqrt(max(mesh_area, 0.0))
                * order_gain
            )
            amp = amp0 * amp_scale / (max(rng, min_range_m) ** float(range_amp_exp))
            path_id = str(obj.get("path_id", f"mesh_{obj_id}_c{int(k):04d}"))

            chirp_paths.append(
                RadarPath(
                    delay_s=float(2.0 * rng / C0),
                    doppler_hz=float(2.0 * radial_v / lam),
                    unit_direction=(float(u[0]), float(u[1]), float(u[2])),
                    amp=complex(amp),
                    path_id=path_id,
                    material_tag=material_tag,
                    reflection_order=reflection_order,
                )
            )
        out.append(chirp_paths)
    return out


def _apply_optional_radar_compensation(
    paths_by_chirp: Sequence[Sequence[RadarPath]],
    backend: Mapping[str, Any],
    radar_cfg: RadarConfig,
    chirp_interval_s: float,
) -> Tuple[List[List[RadarPath]], Dict[str, Any]]:
    cfg = backend.get("radar_compensation")
    if cfg is None:
        return [list(row) for row in paths_by_chirp], {
            "enabled": False,
            "input_path_count": int(sum(len(row) for row in paths_by_chirp)),
            "output_path_count": int(sum(len(row) for row in paths_by_chirp)),
            "added_diffuse_path_count": 0,
            "added_clutter_path_count": 0,
            "seed": None,
            "reason": "not_configured",
        }
    if not isinstance(cfg, Mapping):
        raise ValueError("backend.radar_compensation must be object")
    compensated, summary = apply_radar_compensation(
        paths_by_chirp=paths_by_chirp,
        radar=radar_cfg,
        chirp_interval_s=float(chirp_interval_s),
        config=cfg,
    )
    return [list(row) for row in compensated], dict(summary)


def _resolve_backend_chirp_interval_s(backend: Mapping[str, Any], radar_cfg: RadarConfig) -> float:
    chirp_interval_s = _opt_float(backend.get("chirp_interval_s"))
    if chirp_interval_s is not None:
        return float(chirp_interval_s)

    runtime_input = backend.get("runtime_input")
    if isinstance(runtime_input, Mapping):
        runtime_chirp = _opt_float(runtime_input.get("chirp_interval_s"))
        if runtime_chirp is not None:
            return float(runtime_chirp)

    return float(radar_cfg.samples_per_chirp) / float(radar_cfg.fs_hz)


def _resolve_positions_3d(payload: Mapping[str, Any], key: str) -> np.ndarray:
    raw = payload.get(key)
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError(f"{key} must be list of [x,y,z]")
    arr = np.asarray(raw, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1] != 3 or arr.shape[0] <= 0:
        raise ValueError(f"{key} must have shape (n,3)")
    return arr


def _resolve_vector3(value: Any, key_name: str) -> np.ndarray:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{key_name} must be [x,y,z]")
    if len(value) != 3:
        raise ValueError(f"{key_name} must have length 3")
    arr = np.asarray(value, dtype=np.float64).reshape(3)
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{key_name} must be finite")
    return arr


def _resolve_velocity_vector(
    obj: Mapping[str, Any],
    obj_idx: int,
    ego_pos_m: np.ndarray,
    pos0: np.ndarray,
) -> np.ndarray:
    if "velocity_mps" in obj:
        return _resolve_vector3(obj.get("velocity_mps"), f"object[{obj_idx}].velocity_mps")
    radial_v = float(obj.get("radial_velocity_mps", 0.0))
    rel0 = pos0 - ego_pos_m
    norm = float(np.linalg.norm(rel0))
    if norm <= 0.0:
        return np.zeros(3, dtype=np.float64)
    return (radial_v * rel0 / norm).astype(np.float64)


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


def _resolve_optional_string_list(value: Any, key_name: str) -> Optional[Tuple[str, ...]]:
    if value is None:
        return None
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{key_name} must be list[str]")
    out = tuple(str(x).strip() for x in value if str(x).strip() != "")
    return out


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
