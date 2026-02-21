import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np

from .antenna import AntennaModel
from .constants import C0
from .types import Path as RadarPath
from .types import RadarConfig


def build_calibration_samples(
    paths_by_chirp: Sequence[Sequence[RadarPath]],
    adc: np.ndarray,
    radar: RadarConfig,
    tx_pos_m: np.ndarray,
    rx_pos_m: np.ndarray,
    antenna_model: AntennaModel,
    observed_mode: str = "normalized",
    max_paths_per_chirp: int = 1,
    min_path_amp: float = 0.0,
    min_base_abs: float = 1e-12,
) -> Dict[str, np.ndarray]:
    """
    Build calibration sample tensors for global Jones fitting.

    Output keys:
      tx_jones      : (N,2) complex128
      rx_jones      : (N,2) complex128
      observed_gain : (N,)  complex128
      path_matrices : (N,2,2) complex128
      chirp_indices : (N,) int64
      tx_indices    : (N,) int64
      rx_indices    : (N,) int64
      path_indices  : (N,) int64
      beat_hz       : (N,) float64
    """
    mode = str(observed_mode).strip().lower()
    if mode not in {"normalized", "raw"}:
        raise ValueError("observed_mode must be one of: normalized, raw")
    if max_paths_per_chirp <= 0:
        raise ValueError("max_paths_per_chirp must be positive")

    cube = np.asarray(adc)
    if cube.ndim != 4:
        raise ValueError("adc must have shape (sample, chirp, tx, rx)")
    n_samp, n_chirp, n_tx, n_rx = cube.shape
    if len(radar.tx_schedule) != n_chirp:
        raise ValueError("radar.tx_schedule length mismatch with adc chirp dimension")
    if len(paths_by_chirp) != n_chirp:
        raise ValueError("paths_by_chirp length mismatch with adc chirp dimension")

    tx_pos = np.asarray(tx_pos_m, dtype=np.float64)
    rx_pos = np.asarray(rx_pos_m, dtype=np.float64)
    if tx_pos.shape != (n_tx, 3):
        raise ValueError("tx_pos_m must have shape (n_tx,3)")
    if rx_pos.shape != (n_rx, 3):
        raise ValueError("rx_pos_m must have shape (n_rx,3)")

    lam = C0 / float(radar.fc_hz)
    fast_time = np.arange(n_samp, dtype=np.float64) / float(radar.fs_hz)

    tx_jones = []
    rx_jones = []
    observed_gain = []
    path_matrices = []
    chirp_indices = []
    tx_indices = []
    rx_indices = []
    path_indices = []
    beat_hz_all = []

    for chirp_idx in range(n_chirp):
        tx_idx = int(radar.tx_schedule[chirp_idx])
        if tx_idx < 0 or tx_idx >= n_tx:
            raise ValueError(f"tx_schedule[{chirp_idx}] out of range: {tx_idx}")
        chirp_paths = list(paths_by_chirp[chirp_idx])
        if not chirp_paths:
            continue

        order = np.argsort([-abs(complex(p.amp)) for p in chirp_paths]).tolist()
        selected = order[: int(max_paths_per_chirp)]

        for path_idx in selected:
            p = chirp_paths[int(path_idx)]
            if abs(complex(p.amp)) < float(min_path_amp):
                continue

            u = _normalize(np.asarray(p.unit_direction, dtype=np.float64))
            ph_tx = np.exp(-1j * 2 * np.pi / lam * np.dot(u, tx_pos[tx_idx]))
            ph_rx = np.exp(-1j * 2 * np.pi / lam * (rx_pos @ u))
            fb = float(radar.slope_hz_per_s) * float(p.delay_s) + float(p.doppler_hz)
            tone = np.exp(1j * 2 * np.pi * fb * fast_time)

            tx_j = np.asarray(antenna_model.tx_jones(tx_idx, p), dtype=np.complex128).reshape(-1)
            rx_j_all = np.asarray(antenna_model.rx_jones(p, n_rx), dtype=np.complex128)
            if tx_j.shape != (2,):
                raise ValueError("antenna_model.tx_jones must return shape (2,)")
            if rx_j_all.shape != (n_rx, 2):
                raise ValueError("antenna_model.rx_jones must return shape (n_rx,2)")
            pmat = _resolve_pol_matrix(p)

            for rx_idx in range(n_rx):
                s = np.asarray(cube[:, chirp_idx, tx_idx, rx_idx], dtype=np.complex128)
                g = np.vdot(tone, s) / float(n_samp)
                if mode == "normalized":
                    base = complex(p.amp) * ph_tx * ph_rx[rx_idx]
                    if abs(base) < float(min_base_abs):
                        continue
                    g = g / base

                tx_jones.append(tx_j.copy())
                rx_jones.append(rx_j_all[rx_idx, :].copy())
                observed_gain.append(complex(g))
                path_matrices.append(pmat.copy())
                chirp_indices.append(int(chirp_idx))
                tx_indices.append(int(tx_idx))
                rx_indices.append(int(rx_idx))
                path_indices.append(int(path_idx))
                beat_hz_all.append(float(fb))

    if not observed_gain:
        raise ValueError("no calibration samples extracted")

    return {
        "tx_jones": np.asarray(tx_jones, dtype=np.complex128),
        "rx_jones": np.asarray(rx_jones, dtype=np.complex128),
        "observed_gain": np.asarray(observed_gain, dtype=np.complex128),
        "path_matrices": np.asarray(path_matrices, dtype=np.complex128),
        "chirp_indices": np.asarray(chirp_indices, dtype=np.int64),
        "tx_indices": np.asarray(tx_indices, dtype=np.int64),
        "rx_indices": np.asarray(rx_indices, dtype=np.int64),
        "path_indices": np.asarray(path_indices, dtype=np.int64),
        "beat_hz": np.asarray(beat_hz_all, dtype=np.float64),
    }


def save_calibration_samples_npz(
    out_npz: str,
    samples: Mapping[str, np.ndarray],
    metadata: Optional[Mapping[str, Any]] = None,
) -> None:
    payload: Dict[str, Any] = {}
    for key, value in samples.items():
        payload[str(key)] = np.asarray(value)
    if metadata is not None:
        payload["metadata_json"] = json.dumps(_to_jsonable(metadata))
    np.savez_compressed(str(out_npz), **payload)


def load_calibration_samples_npz(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    out: Dict[str, Any] = {}
    with np.load(str(p), allow_pickle=False) as payload:
        for key in payload.files:
            if key == "metadata_json":
                out[key] = json.loads(str(payload[key].tolist()))
            else:
                out[key] = payload[key]
    return out


def _normalize(vec: np.ndarray) -> np.ndarray:
    x = np.asarray(vec, dtype=np.float64).reshape(-1)
    if x.size != 3:
        raise ValueError("unit_direction must have length 3")
    norm = float(np.linalg.norm(x))
    if norm <= 0:
        raise ValueError("unit_direction norm must be positive")
    return x / norm


def _resolve_pol_matrix(path: RadarPath) -> np.ndarray:
    if path.pol_matrix is None:
        return np.eye(2, dtype=np.complex128)
    arr = np.asarray(list(path.pol_matrix), dtype=np.complex128).reshape(-1)
    if arr.size != 4:
        raise ValueError("path.pol_matrix must have 4 entries")
    return arr.reshape(2, 2)


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, (np.complexfloating, complex)):
        return {"re": float(np.real(value)), "im": float(np.imag(value))}
    return value

