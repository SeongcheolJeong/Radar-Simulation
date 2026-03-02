import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np

from .path_contract import validate_paths_by_chirp
from .types import Path as RadarPath
from .types import RadarConfig


def save_paths_by_chirp_json(paths_by_chirp: Sequence[Sequence[RadarPath]], out_json: str) -> None:
    validate_paths_by_chirp(
        paths_by_chirp=paths_by_chirp,
        n_chirps=None,
        require_metadata=True,
    )
    out: List[List[Dict[str, Any]]] = []
    for chirp_paths in paths_by_chirp:
        row: List[Dict[str, Any]] = []
        for p in chirp_paths:
            item = {
                "delay_s": float(p.delay_s),
                "doppler_hz": float(p.doppler_hz),
                "unit_direction": [float(x) for x in p.unit_direction],
                "amp_complex": {"re": float(np.real(p.amp)), "im": float(np.imag(p.amp))},
            }
            if p.path_id is not None and str(p.path_id).strip() != "":
                item["path_id"] = str(p.path_id)
            if p.material_tag is not None and str(p.material_tag).strip() != "":
                item["material_tag"] = str(p.material_tag)
            if p.reflection_order is not None:
                item["reflection_order"] = int(p.reflection_order)
            if p.pol_matrix is not None:
                pm = np.asarray(list(p.pol_matrix), dtype=np.complex128).reshape(-1)
                if pm.size == 4:
                    item["pol_matrix"] = [
                        {"re": float(np.real(x)), "im": float(np.imag(x))} for x in pm
                    ]
            row.append(item)
        out.append(row)
    Path(out_json).write_text(json.dumps(out, indent=2), encoding="utf-8")


def save_adc_npz(
    adc: np.ndarray,
    radar: RadarConfig,
    tx_pos_m: np.ndarray,
    rx_pos_m: np.ndarray,
    out_npz: str,
) -> None:
    metadata = {
        "fc_hz": float(radar.fc_hz),
        "slope_hz_per_s": float(radar.slope_hz_per_s),
        "fs_hz": float(radar.fs_hz),
        "samples_per_chirp": int(radar.samples_per_chirp),
        "tx_schedule": [int(x) for x in radar.tx_schedule],
        "tx_pos_m": np.asarray(tx_pos_m, dtype=np.float64).tolist(),
        "rx_pos_m": np.asarray(rx_pos_m, dtype=np.float64).tolist(),
    }
    np.savez_compressed(out_npz, adc=adc, metadata_json=json.dumps(metadata))


def save_hybrid_estimation_npz(
    estimation: Dict[str, Any],
    out_npz: str,
    metadata: Dict[str, Any],
) -> None:
    payload: Dict[str, Any] = {"metadata_json": json.dumps(metadata)}
    for key, value in estimation.items():
        if isinstance(value, np.ndarray):
            payload[key] = value
        elif isinstance(value, (int, float)):
            payload[key] = np.asarray(value)
        else:
            # Non-array outputs are encoded into metadata.
            metadata[key] = value
    payload["metadata_json"] = json.dumps(metadata)
    np.savez_compressed(out_npz, **payload)
