from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

import numpy as np

from .adapters import load_hybrid_paths_from_frames, load_hybrid_radar_geometry
from .io import save_adc_npz, save_paths_by_chirp_json
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

    if output_dir is not None:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        paths_json = out_dir / "path_list.json"
        adc_npz = out_dir / "adc_cube.npz"
        save_paths_by_chirp_json(paths_by_chirp, str(paths_json))
        save_adc_npz(adc, radar, tx_pos, rx_pos, str(adc_npz))
        result["path_list_json"] = str(paths_json)
        result["adc_cube_npz"] = str(adc_npz)

    return result

