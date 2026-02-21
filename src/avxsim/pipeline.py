from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

import numpy as np

from .adapters import load_hybrid_paths_from_frames, load_hybrid_radar_geometry
from .hybrid_pcode import run_hybrid_estimation_bundle
from .io import save_adc_npz, save_hybrid_estimation_npz, save_paths_by_chirp_json
from .synth import synth_fmcw_tdm
from .types import RadarConfig


def run_hybrid_frames_pipeline(
    frames_root_dir: str,
    radar_json_path: str,
    frame_indices: Sequence[int],
    fc_hz: float,
    slope_hz_per_s: float,
    fs_hz: float,
    samples_per_chirp: int,
    camera_fov_deg: float,
    mode: str = "reflection",
    file_ext: str = ".exr",
    camera_rotate_deg: Tuple[float, float] = (0.0, 0.0),
    amplitude_threshold: float = 0.0,
    distance_limits_m: Tuple[float, float] = (0.0, 100.0),
    amplitude_scale: float = 1.0,
    top_k_per_chirp: Optional[int] = None,
    run_hybrid_estimation: bool = False,
    estimation_nfft: int = 144,
    estimation_range_bin_length: int = 10,
    estimation_doppler_window: str = "hann",
    output_dir: Optional[str] = None,
) -> Dict[str, object]:
    tx_pos, rx_pos = load_hybrid_radar_geometry(radar_json_path)
    n_tx = tx_pos.shape[0]

    tx_schedule = [i % n_tx for i in range(len(frame_indices))]
    radar = RadarConfig(
        fc_hz=fc_hz,
        slope_hz_per_s=slope_hz_per_s,
        fs_hz=fs_hz,
        samples_per_chirp=samples_per_chirp,
        tx_schedule=tx_schedule,
    )

    paths_by_chirp = load_hybrid_paths_from_frames(
        root_dir=frames_root_dir,
        frame_indices=frame_indices,
        camera_fov_deg=camera_fov_deg,
        mode=mode,
        camera_rotate_deg=camera_rotate_deg,
        file_ext=file_ext,
        amplitude_threshold=amplitude_threshold,
        distance_limits_m=distance_limits_m,
        amplitude_scale=amplitude_scale,
        top_k_per_chirp=top_k_per_chirp,
    )

    adc = synth_fmcw_tdm(
        paths_by_chirp=paths_by_chirp,
        tx_pos_m=tx_pos,
        rx_pos_m=rx_pos,
        radar=radar,
    )

    result: Dict[str, object] = {
        "paths_by_chirp": paths_by_chirp,
        "adc": adc,
        "tx_pos_m": tx_pos,
        "rx_pos_m": rx_pos,
        "tx_schedule": tx_schedule,
    }

    if run_hybrid_estimation:
        h = _build_h_from_adc_tdm(adc, tx_schedule)
        angle_view_cali = _compute_angle_view_cali(
            camera_fov_deg=camera_fov_deg,
            camera_rotate_deg=camera_rotate_deg,
        )
        estimation = run_hybrid_estimation_bundle(
            h=h,
            np_chirps=len(tx_schedule),
            ns=int(samples_per_chirp),
            nfft=int(estimation_nfft),
            num_tx=int(tx_pos.shape[0]),
            num_rx=int(rx_pos.shape[0]),
            angle_view_cali=angle_view_cali,
            range_bin_length=int(estimation_range_bin_length),
            doppler_window=estimation_doppler_window,
        )
        result["hybrid_estimation"] = estimation

    if output_dir is not None:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        paths_json = out_dir / "path_list.json"
        adc_npz = out_dir / "adc_cube.npz"
        save_paths_by_chirp_json(paths_by_chirp, str(paths_json))
        save_adc_npz(adc, radar, tx_pos, rx_pos, str(adc_npz))
        result["path_list_json"] = str(paths_json)
        result["adc_cube_npz"] = str(adc_npz)
        if run_hybrid_estimation:
            est_npz = out_dir / "hybrid_estimation.npz"
            metadata = {
                "nfft": int(estimation_nfft),
                "range_bin_length": int(estimation_range_bin_length),
                "doppler_window": str(estimation_doppler_window),
                "angle_view_cali": list(_compute_angle_view_cali(camera_fov_deg, camera_rotate_deg)),
            }
            save_hybrid_estimation_npz(
                estimation=result["hybrid_estimation"],
                out_npz=str(est_npz),
                metadata=metadata,
            )
            result["hybrid_estimation_npz"] = str(est_npz)

    return result


def _build_h_from_adc_tdm(adc: np.ndarray, tx_schedule: Sequence[int]) -> np.ndarray:
    """
    Convert canonical ADC cube to Hybrid-compatible H layout:
      adc[sample, chirp, tx, rx] -> H[(tx*rx*chirp), sample]
    """
    if adc.ndim != 4:
        raise ValueError("adc must have shape (sample, chirp, tx, rx)")
    n_samp, n_chirp, n_tx, n_rx = adc.shape
    if len(tx_schedule) != n_chirp:
        raise ValueError("tx_schedule length must match chirp dimension")

    cube = np.zeros((n_tx * n_rx, n_chirp, n_samp), dtype=np.complex128)
    for chirp_idx, tx_idx in enumerate(tx_schedule):
        if tx_idx < 0 or tx_idx >= n_tx:
            raise ValueError(f"tx_schedule[{chirp_idx}] out of range: {tx_idx}")
        for rx_idx in range(n_rx):
            channel_idx = tx_idx * n_rx + rx_idx
            cube[channel_idx, chirp_idx, :] = adc[:, chirp_idx, tx_idx, rx_idx]
    return cube.reshape(n_tx * n_rx * n_chirp, n_samp)


def _compute_angle_view_cali(
    camera_fov_deg: float,
    camera_rotate_deg: Tuple[float, float],
) -> Tuple[float, float]:
    az_rot = float(camera_rotate_deg[0])
    left = (camera_fov_deg / 2.0 + az_rot) - camera_fov_deg
    right = abs((camera_fov_deg / 2.0 - az_rot - camera_fov_deg))
    return (float(left), float(right))
