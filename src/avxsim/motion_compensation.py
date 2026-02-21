from typing import Optional, Sequence

import numpy as np

from .hybrid_pcode import doppler_estimation_from_channel


def estimate_doppler_peak_hz(
    h: np.ndarray,
    np_chirps: int,
    nfft: int,
    chirp_interval_s: float,
    window: str = "hann",
) -> float:
    if float(chirp_interval_s) <= 0.0:
        raise ValueError("chirp_interval_s must be positive")
    fx_dop, fx_dop_win = doppler_estimation_from_channel(
        h=h,
        np_chirps=int(np_chirps),
        nfft=int(nfft),
        window=window,
    )
    power = np.sum(fx_dop_win if fx_dop_win is not None else fx_dop, axis=1)
    dop_bins = np.fft.fftshift(np.fft.fftfreq(int(nfft), d=float(chirp_interval_s)))
    return float(dop_bins[int(np.argmax(power))])


def infer_tx_slot_offsets(
    tx_schedule: Sequence[int],
    num_tx: int,
    chirp_interval_s: float,
    reference_tx: Optional[int] = None,
) -> np.ndarray:
    if int(num_tx) <= 0:
        raise ValueError("num_tx must be positive")
    if float(chirp_interval_s) <= 0.0:
        raise ValueError("chirp_interval_s must be positive")
    if len(tx_schedule) <= 0:
        raise ValueError("tx_schedule must be non-empty")

    first_idx = np.full((int(num_tx),), -1, dtype=np.int64)
    for i, tx in enumerate(tx_schedule):
        t = int(tx)
        if t < 0 or t >= int(num_tx):
            raise ValueError(f"tx_schedule[{i}] out of range: {t}")
        if first_idx[t] < 0:
            first_idx[t] = i
    ref = int(tx_schedule[0]) if reference_tx is None else int(reference_tx)
    if ref < 0 or ref >= int(num_tx):
        raise ValueError(f"reference_tx out of range: {ref}")
    if first_idx[ref] < 0:
        raise ValueError("reference_tx does not appear in tx_schedule")
    ref_idx = int(first_idx[ref])
    # If some Tx IDs do not appear in this short schedule, keep zero relative offset.
    first_idx[first_idx < 0] = ref_idx
    offsets = (first_idx.astype(np.float64) - float(ref_idx)) * float(chirp_interval_s)
    return offsets


def apply_tdm_motion_compensation_to_h(
    h: np.ndarray,
    np_chirps: int,
    num_tx: int,
    num_rx: int,
    tx_schedule: Sequence[int],
    doppler_hz: float,
    chirp_interval_s: float,
    reference_tx: Optional[int] = None,
) -> np.ndarray:
    x = np.asarray(h, dtype=np.complex128)
    if x.ndim != 2:
        raise ValueError("h must be 2D")
    if int(np_chirps) <= 0:
        raise ValueError("np_chirps must be positive")
    if int(num_tx) <= 0 or int(num_rx) <= 0:
        raise ValueError("num_tx and num_rx must be positive")
    n_virtual = int(num_tx) * int(num_rx)
    if x.shape[0] != n_virtual * int(np_chirps):
        raise ValueError("h shape mismatch against num_tx*num_rx*np_chirps")

    offsets = infer_tx_slot_offsets(
        tx_schedule=tx_schedule,
        num_tx=int(num_tx),
        chirp_interval_s=float(chirp_interval_s),
        reference_tx=reference_tx,
    )

    cube = x.reshape(n_virtual, int(np_chirps), x.shape[1]).copy()
    for tx_idx in range(int(num_tx)):
        phase = np.exp(-1j * 2.0 * np.pi * float(doppler_hz) * float(offsets[tx_idx]))
        c0 = tx_idx * int(num_rx)
        c1 = (tx_idx + 1) * int(num_rx)
        cube[c0:c1, :, :] *= phase
    return cube.reshape(x.shape)
