from typing import Optional, Sequence

import numpy as np

from .antenna import AntennaModel, IsotropicAntenna
from .constants import C0
from .path_contract import validate_paths_by_chirp
from .types import Path, RadarConfig


def _normalize(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    if norm <= 0:
        raise ValueError("unit_direction must be non-zero")
    return vec / norm


def synth_fmcw_tdm(
    paths_by_chirp: Sequence[Sequence[Path]],
    tx_pos_m: np.ndarray,
    rx_pos_m: np.ndarray,
    radar: RadarConfig,
    antenna_model: Optional[AntennaModel] = None,
    use_jones_polarization: bool = False,
    global_jones_matrix: Optional[np.ndarray] = None,
    noise_sigma: float = 0.0,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """
    Returns canonical cube: adc[sample, chirp, tx, rx] complex64
    """
    if antenna_model is None:
        antenna_model = IsotropicAntenna()

    tx_pos = np.asarray(tx_pos_m, dtype=np.float64)
    rx_pos = np.asarray(rx_pos_m, dtype=np.float64)

    if tx_pos.ndim != 2 or tx_pos.shape[1] != 3:
        raise ValueError("tx_pos_m must have shape (n_tx, 3)")
    if rx_pos.ndim != 2 or rx_pos.shape[1] != 3:
        raise ValueError("rx_pos_m must have shape (n_rx, 3)")

    n_tx = tx_pos.shape[0]
    n_rx = rx_pos.shape[0]
    n_chirps = len(radar.tx_schedule)
    n_samp = int(radar.samples_per_chirp)

    validate_paths_by_chirp(
        paths_by_chirp=paths_by_chirp,
        n_chirps=n_chirps,
        require_metadata=False,
    )
    if len(paths_by_chirp) != n_chirps:
        raise ValueError("paths_by_chirp length must match tx_schedule length")
    if global_jones_matrix is not None and not use_jones_polarization:
        raise ValueError("global_jones_matrix requires use_jones_polarization=True")
    j_global = _resolve_jones_matrix(global_jones_matrix)

    lam = C0 / float(radar.fc_hz)
    fast_time = np.arange(n_samp, dtype=np.float64) / float(radar.fs_hz)

    adc = np.zeros((n_samp, n_chirps, n_tx, n_rx), dtype=np.complex64)

    for chirp_idx, tx_idx in enumerate(radar.tx_schedule):
        if tx_idx < 0 or tx_idx >= n_tx:
            raise ValueError(f"tx_schedule[{chirp_idx}] out of range: {tx_idx}")

        for path in paths_by_chirp[chirp_idx]:
            u = _normalize(np.asarray(path.unit_direction, dtype=np.float64))
            ph_tx = np.exp(-1j * 2 * np.pi / lam * np.dot(u, tx_pos[tx_idx]))
            ph_rx = np.exp(-1j * 2 * np.pi / lam * (rx_pos @ u))

            if use_jones_polarization:
                tx_j = np.asarray(antenna_model.tx_jones(tx_idx, path), dtype=np.complex128).reshape(-1)
                rx_j = np.asarray(antenna_model.rx_jones(path, n_rx), dtype=np.complex128)
                if tx_j.shape != (2,):
                    raise ValueError("tx_jones must return shape (2,)")
                if rx_j.shape != (n_rx, 2):
                    raise ValueError("rx_jones must return shape (n_rx, 2)")
                j_path = _resolve_pol_matrix(path)
                if j_global is not None:
                    j_path = j_global @ j_path
                pol_gain = np.einsum("ri,ij,j->r", np.conj(rx_j), j_path, tx_j)
                path_amp = complex(path.amp) * ph_tx * ph_rx * pol_gain
            else:
                g_tx = complex(antenna_model.tx_gain(tx_idx, path))
                g_rx = np.asarray(antenna_model.rx_gain(path, n_rx), dtype=np.complex128)
                if g_rx.shape != (n_rx,):
                    raise ValueError("rx_gain must return shape (n_rx,)")
                path_amp = complex(path.amp) * ph_tx * ph_rx * g_tx * g_rx

            beat_hz = float(radar.slope_hz_per_s) * float(path.delay_s) + float(path.doppler_hz)
            tone = np.exp(1j * 2 * np.pi * beat_hz * fast_time)
            adc[:, chirp_idx, tx_idx, :] += (tone[:, None] * path_amp[None, :]).astype(np.complex64)

    if noise_sigma > 0:
        if rng is None:
            rng = np.random.default_rng()
        noise = rng.standard_normal(adc.shape) + 1j * rng.standard_normal(adc.shape)
        adc += (noise_sigma / np.sqrt(2.0)) * noise.astype(np.complex64)

    return adc


def reshape_virtual_channels(adc: np.ndarray) -> np.ndarray:
    """
    Convert canonical cube to virtual channels:
    input:  adc[sample, chirp, tx, rx]
    output: virtual[sample, chirp, channel] where channel = tx*n_rx + rx
    """
    if adc.ndim != 4:
        raise ValueError("adc must have shape (sample, chirp, tx, rx)")
    n_samp, n_chirp, n_tx, n_rx = adc.shape
    return adc.reshape(n_samp, n_chirp, n_tx * n_rx)


def _resolve_pol_matrix(path: Path) -> np.ndarray:
    if path.pol_matrix is None:
        return np.eye(2, dtype=np.complex128)
    p = path.pol_matrix
    if isinstance(p, np.ndarray):
        arr = np.asarray(p, dtype=np.complex128)
    else:
        arr = np.asarray(list(p), dtype=np.complex128)
    if arr.shape == (2, 2):
        return arr
    if arr.shape == (4,):
        return arr.reshape(2, 2)
    raise ValueError("path.pol_matrix must be shape (2,2) or length 4")


def _resolve_jones_matrix(value: Optional[np.ndarray]) -> Optional[np.ndarray]:
    if value is None:
        return None
    arr = np.asarray(value, dtype=np.complex128)
    if arr.shape == (2, 2):
        return arr
    if arr.shape == (4,):
        return arr.reshape(2, 2)
    raise ValueError("global_jones_matrix must be shape (2,2) or length 4")
