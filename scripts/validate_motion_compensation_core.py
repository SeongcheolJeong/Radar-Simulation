#!/usr/bin/env python3
import numpy as np

from avxsim.hybrid_pcode import angle_estimation_from_channel
from avxsim.motion_compensation import (
    apply_tdm_motion_compensation_to_h,
    estimate_doppler_peak_hz,
)


def _build_h(
    n_virtual: int,
    np_chirps: int,
    ns: int,
    range_bin: int,
    steering: np.ndarray,
    slow_phase: np.ndarray,
    tx_phase: np.ndarray,
    num_rx: int,
) -> np.ndarray:
    cube = np.zeros((n_virtual, np_chirps, ns), dtype=np.complex128)
    for ch in range(n_virtual):
        tx_idx = ch // num_rx
        sig = steering[ch] * tx_phase[tx_idx] * slow_phase
        cube[ch, :, range_bin] = sig
    return cube.reshape(n_virtual * np_chirps, ns)


def _angle_peak_bin(h, np_chirps, ns, nfft, num_tx, num_rx):
    _, cap, ncap = angle_estimation_from_channel(
        h=h,
        np_chirps=np_chirps,
        ns=ns,
        nfft=nfft,
        num_tx=num_tx,
        num_rx=num_rx,
        angle_view_cali=(-45.0, 45.0),
    )
    assert cap.shape[1] == ncap
    # Range bin 10 is where we injected signal.
    return int(np.argmax(cap[10, :])), cap[10, :]


def run() -> None:
    num_tx = 2
    num_rx = 4
    n_virtual = num_tx * num_rx
    np_chirps = 16
    ns = 64
    nfft = 64
    range_bin = 10

    chirp_interval_s = 50e-6
    fd_hz_true = 3750.0  # exact FFT bin for nfft=64, Tc=50us
    tx_schedule = [i % num_tx for i in range(np_chirps)]

    # True array manifold
    true_spatial_bin = 2
    ch_idx = np.arange(n_virtual, dtype=np.float64)
    steering = np.exp(1j * 2 * np.pi * true_spatial_bin * ch_idx / n_virtual)

    k = np.arange(np_chirps, dtype=np.float64)
    slow_phase = np.exp(1j * 2 * np.pi * fd_hz_true * k * chirp_interval_s)

    # Reference: no TDM phase distortion
    h_ref = _build_h(
        n_virtual=n_virtual,
        np_chirps=np_chirps,
        ns=ns,
        range_bin=range_bin,
        steering=steering,
        slow_phase=slow_phase,
        tx_phase=np.asarray([1.0 + 0.0j, 1.0 + 0.0j], dtype=np.complex128),
        num_rx=num_rx,
    )
    peak_ref, vec_ref = _angle_peak_bin(
        h_ref, np_chirps=np_chirps, ns=ns, nfft=nfft, num_tx=num_tx, num_rx=num_rx
    )

    # Distorted: Tx1 has additional Doppler-induced slot phase
    tx_slot_phase = np.exp(1j * 2 * np.pi * fd_hz_true * chirp_interval_s)
    h_dist = _build_h(
        n_virtual=n_virtual,
        np_chirps=np_chirps,
        ns=ns,
        range_bin=range_bin,
        steering=steering,
        slow_phase=slow_phase,
        tx_phase=np.asarray([1.0 + 0.0j, tx_slot_phase], dtype=np.complex128),
        num_rx=num_rx,
    )

    fd_est = estimate_doppler_peak_hz(
        h=h_dist,
        np_chirps=np_chirps,
        nfft=nfft,
        chirp_interval_s=chirp_interval_s,
        window="hann",
    )
    assert abs(fd_est - fd_hz_true) < 1e-6, (fd_est, fd_hz_true)

    peak_dist, vec_dist = _angle_peak_bin(
        h_dist, np_chirps=np_chirps, ns=ns, nfft=nfft, num_tx=num_tx, num_rx=num_rx
    )

    h_comp = apply_tdm_motion_compensation_to_h(
        h=h_dist,
        np_chirps=np_chirps,
        num_tx=num_tx,
        num_rx=num_rx,
        tx_schedule=tx_schedule,
        doppler_hz=fd_est,
        chirp_interval_s=chirp_interval_s,
        reference_tx=0,
    )
    peak_comp, vec_comp = _angle_peak_bin(
        h_comp, np_chirps=np_chirps, ns=ns, nfft=nfft, num_tx=num_tx, num_rx=num_rx
    )

    # Compensation should recover reference peak and improve power at that peak.
    assert peak_comp == peak_ref, (peak_comp, peak_ref)
    assert np.real(vec_comp[peak_ref]) > np.real(vec_dist[peak_ref])
    assert np.real(vec_comp[peak_ref]) >= 0.9 * np.real(vec_ref[peak_ref])

    print("Motion compensation core validation passed.")


if __name__ == "__main__":
    run()

