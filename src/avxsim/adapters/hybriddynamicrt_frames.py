import json
import re
from pathlib import Path
from typing import Any, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from ..constants import C0
from ..path_power_tuning import predict_path_power_amplitude_from_fit
from ..types import Path as RadarPath


def load_hybrid_radar_geometry(
    radar_json_path: str,
    camera_loc_m: Tuple[float, float, float] = (0.0, 0.0, 1.2),
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load Tx/Rx positions from HybridDynamicRT radar_parameters_hybrid.json.
    Returns:
      tx_pos_m: (n_tx, 3)
      rx_pos_m: (n_rx, 3)
    """
    p = Path(radar_json_path)
    payload = json.loads(p.read_text(encoding="utf-8"))

    tx_offsets = payload.get("antenna_offsets_tx", {})
    rx_offsets = payload.get("antenna_offsets_rx", {})

    tx_pos = _build_positions_from_offsets(tx_offsets, prefix="Tx", camera_loc_m=camera_loc_m)
    rx_pos = _build_positions_from_offsets(rx_offsets, prefix="Rx", camera_loc_m=camera_loc_m)
    return tx_pos, rx_pos


def _build_positions_from_offsets(offsets: dict, prefix: str, camera_loc_m: Tuple[float, float, float]) -> np.ndarray:
    if not isinstance(offsets, dict) or not offsets:
        raise ValueError(f"{prefix} offsets are missing or empty")

    keys = sorted(offsets.keys(), key=_extract_suffix_index)
    out = np.zeros((len(keys), 3), dtype=np.float64)
    cam = np.asarray(camera_loc_m, dtype=np.float64)

    for i, key in enumerate(keys):
        val = offsets[key]
        if not isinstance(val, (list, tuple)) or len(val) != 3:
            raise ValueError(f"invalid offset for {key}: expected length-3 list")
        out[i, :] = cam + np.asarray(val, dtype=np.float64)
    return out


def _extract_suffix_index(name: str) -> int:
    m = re.search(r"(\d+)$", name)
    if not m:
        raise ValueError(f"name does not end with numeric index: {name}")
    return int(m.group(1))


def load_hybrid_paths_from_frames(
    root_dir: str,
    frame_indices: Sequence[int],
    camera_fov_deg: float,
    mode: str = "reflection",
    camera_rotate_deg: Tuple[float, float] = (0.0, 0.0),
    pair: Optional[Tuple[int, int]] = None,
    file_ext: str = ".exr",
    amplitude_prefix: str = "AmplitudeOutput",
    distance_prefix: Optional[str] = None,
    distance_scale: Optional[float] = None,
    amplitude_threshold: float = 0.0,
    distance_limits_m: Tuple[float, float] = (0.0, 100.0),
    amplitude_scale: float = 1.0,
    top_k_per_chirp: Optional[int] = None,
    path_power_fit_payload: Optional[Mapping[str, Any]] = None,
    path_power_apply_mode: str = "shape_only",
) -> List[List[RadarPath]]:
    """
    Parse HybridDynamicRT-style Blender frame outputs into paths_by_chirp.

    Expected per-pair directory:
      Tx{tx}Rx{rx}/{amplitude_prefix}####{file_ext}
      Tx{tx}Rx{rx}/{distance_prefix or mode-default}####{file_ext}

    Notes:
    - DistanceOutput is treated as round-trip distance in meters.
    - Depth is treated as one-way distance and internally multiplied by 2.
    """
    root = Path(root_dir)
    if pair is None:
        pair_dir = _resolve_pair_dir(root)
    else:
        pair_dir = root / f"Tx{pair[0]}Rx{pair[1]}"
        if not pair_dir.is_dir():
            raise FileNotFoundError(f"pair directory not found: {pair_dir}")

    if mode == "reflection":
        default_dist_prefix = "DistanceOutput"
        default_dist_scale = 1.0
    elif mode == "scattering":
        default_dist_prefix = "Depth"
        default_dist_scale = 2.0
    else:
        raise ValueError("mode must be 'reflection' or 'scattering'")
    amp_prefix = str(amplitude_prefix).strip()
    if amp_prefix == "":
        raise ValueError("amplitude_prefix must be non-empty")
    dist_prefix = (
        default_dist_prefix if distance_prefix is None else str(distance_prefix).strip()
    )
    if dist_prefix == "":
        raise ValueError("distance_prefix must be non-empty")
    dist_scale = (
        default_dist_scale if distance_scale is None else float(distance_scale)
    )
    if not np.isfinite(dist_scale) or dist_scale <= 0.0:
        raise ValueError("distance_scale must be finite and > 0")

    first_amp = _load_frame_2d(pair_dir / f"{amp_prefix}{int(frame_indices[0]):04d}{file_ext}")
    pixel_h, pixel_w = first_amp.shape
    dir_lut = _build_unit_directions(
        pixel_width=pixel_w,
        pixel_height=pixel_h,
        camera_fov_deg=camera_fov_deg,
        camera_rotate_deg=camera_rotate_deg,
    )

    dmin, dmax = float(distance_limits_m[0]), float(distance_limits_m[1])
    out: List[List[RadarPath]] = []
    apply_mode = str(path_power_apply_mode).strip().lower()
    if apply_mode not in {"shape_only", "replace"}:
        raise ValueError("path_power_apply_mode must be one of: shape_only, replace")
    if path_power_fit_payload is not None:
        fit_obj = path_power_fit_payload.get("fit", None) if isinstance(path_power_fit_payload, Mapping) else None
        if not isinstance(fit_obj, Mapping):
            raise ValueError("path_power_fit_payload must include fit object")
        fit_model = str(fit_obj.get("model", "")).strip().lower()
        if fit_model not in {"reflection", "scattering"}:
            raise ValueError("path_power_fit_payload fit.model must be reflection/scattering")
        if fit_model != str(mode):
            raise ValueError(
                f"path power fit model '{fit_model}' does not match ingest mode '{mode}'"
            )

    for frame_idx in frame_indices:
        amp_map = _load_frame_2d(pair_dir / f"{amp_prefix}{int(frame_idx):04d}{file_ext}")
        dist_map = _load_frame_2d(pair_dir / f"{dist_prefix}{int(frame_idx):04d}{file_ext}") * dist_scale

        if amp_map.shape != (pixel_h, pixel_w) or dist_map.shape != (pixel_h, pixel_w):
            raise ValueError("all frame maps must share a fixed 2D shape")

        amp_vec = _flatten_like_matlab(amp_map).astype(np.float64)
        dist_vec = _flatten_like_matlab(dist_map).astype(np.float64)

        mask = np.isfinite(amp_vec) & np.isfinite(dist_vec)
        mask &= (dist_vec > dmin) & (dist_vec < dmax)
        mask &= np.abs(amp_vec) > float(amplitude_threshold)

        idx = np.flatnonzero(mask)
        if top_k_per_chirp is not None and idx.size > int(top_k_per_chirp):
            strengths = np.abs(amp_vec[idx])
            keep_rel = np.argpartition(strengths, -int(top_k_per_chirp))[-int(top_k_per_chirp) :]
            idx = idx[keep_rel]

        amp_selected = float(amplitude_scale) * amp_vec[idx]
        if path_power_fit_payload is not None and idx.size > 0:
            dsel = dist_vec[idx]
            r_oneway = np.maximum(dsel / 2.0, 1e-9)
            u = dir_lut[idx]
            az = np.arctan2(u[:, 1], u[:, 0])
            el = np.arcsin(np.clip(u[:, 2], -1.0, 1.0))
            model_amp = predict_path_power_amplitude_from_fit(
                range_m=r_oneway,
                az_rad=az,
                el_rad=el,
                fit_payload=path_power_fit_payload,
            )
            model_amp = np.maximum(np.asarray(model_amp, dtype=np.float64), np.finfo(np.float64).tiny)
            if apply_mode == "replace":
                sign = np.sign(amp_selected)
                sign[sign == 0] = 1.0
                amp_selected = sign * model_amp
            else:
                norm = float(np.median(np.abs(model_amp)))
                if norm <= 0:
                    norm = float(np.mean(np.abs(model_amp)))
                norm = max(norm, float(np.finfo(np.float64).tiny))
                amp_selected = amp_selected * (model_amp / norm)

        chirp_paths: List[RadarPath] = []
        for j, i in enumerate(idx):
            chirp_paths.append(
                RadarPath(
                    delay_s=float(dist_vec[i] / C0),
                    doppler_hz=0.0,
                    unit_direction=(
                        float(dir_lut[i, 0]),
                        float(dir_lut[i, 1]),
                        float(dir_lut[i, 2]),
                    ),
                    amp=complex(float(amp_selected[j]), 0.0),
                )
            )
        out.append(chirp_paths)
    return out


def _resolve_pair_dir(root: Path) -> Path:
    default = root / "Tx0Rx0"
    if default.is_dir():
        return default
    candidates = sorted([p for p in root.glob("Tx*Rx*") if p.is_dir()])
    if not candidates:
        raise FileNotFoundError(f"no Tx*Rx* directories found under {root}")
    return candidates[0]


def _flatten_like_matlab(img_2d: np.ndarray) -> np.ndarray:
    return np.flipud(img_2d).reshape(-1, order="F")


def _build_unit_directions(
    pixel_width: int,
    pixel_height: int,
    camera_fov_deg: float,
    camera_rotate_deg: Tuple[float, float],
) -> np.ndarray:
    # Replicates the structure in fun_hybrid_pixel_angle.m
    view_left = (camera_fov_deg / 2.0 + camera_rotate_deg[0]) - camera_fov_deg
    view_right = abs((camera_fov_deg / 2.0 - camera_rotate_deg[0] - camera_fov_deg))
    angle_vec_deg = np.linspace(view_left, view_right, num=pixel_width, dtype=np.float64)
    angle_vec_rad = np.deg2rad(angle_vec_deg)

    az = np.zeros((pixel_height, pixel_width), dtype=np.float64)
    el = np.zeros((pixel_height, pixel_width), dtype=np.float64)

    for c in range(pixel_width):
        az[:, c] = (np.pi / 2.0) - angle_vec_rad[c]
    for r in range(pixel_height):
        src_idx = min(r, pixel_width - 1)
        el[r, :] = (np.pi / 2.0) - angle_vec_rad[src_idx]

    az_vec = _flatten_like_matlab(az)
    el_vec = _flatten_like_matlab(el)
    ux = np.cos(el_vec) * np.cos(az_vec)
    uy = np.cos(el_vec) * np.sin(az_vec)
    uz = np.sin(el_vec)
    return np.stack([ux, uy, uz], axis=1)


def _load_frame_2d(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(f"missing frame file: {path}")

    suffix = path.suffix.lower()
    if suffix == ".npy":
        arr = np.load(path)
    elif suffix == ".npz":
        npz = np.load(path)
        if "arr_0" not in npz:
            raise ValueError(f"npz file must contain arr_0: {path}")
        arr = npz["arr_0"]
    else:
        arr = _load_exr_or_image(path)

    arr = np.asarray(arr)
    if arr.ndim == 3:
        arr = arr[:, :, 0]
    if arr.ndim != 2:
        raise ValueError(f"expected 2D (or HxWxC) image, got shape {arr.shape} at {path}")
    return arr.astype(np.float64)


def _load_exr_or_image(path: Path) -> np.ndarray:
    try:
        import imageio.v3 as iio
    except Exception as exc:
        raise ImportError(
            "imageio is required to read EXR/image frames. "
            "Install with: python3 -m pip install --user imageio"
        ) from exc
    return iio.imread(path)
