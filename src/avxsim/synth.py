from typing import Optional, Sequence

import numpy as np

from .antenna import AntennaModel, IsotropicAntenna
from .constants import C0
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

    if len(paths_by_chirp) != n_chirps:
        raise ValueError("paths_by_chirp length must match tx_schedule length")

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

