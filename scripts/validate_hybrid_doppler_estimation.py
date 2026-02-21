#!/usr/bin/env python3
import numpy as np

from avxsim.hybrid_pcode import doppler_estimation_from_channel


def _build_h_with_known_doppler(
    n_virtual: int,
    np_chirps: int,
    n_range: int,
    doppler_bins_by_range: dict,
) -> np.ndarray:
    cube = np.zeros((n_virtual, np_chirps, n_range), dtype=np.complex128)
    chirp_idx = np.arange(np_chirps, dtype=np.float64)

    for rng_bin, dop_bin in doppler_bins_by_range.items():
        for v in range(n_virtual):
            ch_phase = np.exp(1j * 2.0 * np.pi * (0.13 * v))
            tone = np.exp(1j * 2.0 * np.pi * dop_bin * chirp_idx / np_chirps)
            cube[v, :, rng_bin] = ch_phase * tone
    return cube.reshape(n_virtual * np_chirps, n_range)


def run() -> None:
    n_virtual = 5
    np_chirps = 64
    nfft = 128
    n_range = 48

    # Unshifted Doppler bins in [-Np/2, Np/2) domain
    expected = {10: 9, 21: -13, 35: 4}
    h = _build_h_with_known_doppler(
        n_virtual=n_virtual,
        np_chirps=np_chirps,
        n_range=n_range,
        doppler_bins_by_range=expected,
    )

    fx, fx_win = doppler_estimation_from_channel(h, np_chirps=np_chirps, nfft=nfft, window="hann")
    assert fx.shape == (nfft, n_range), fx.shape
    assert fx_win.shape == (nfft, n_range), fx_win.shape
    assert np.all(fx >= 0.0)
    assert np.all(fx_win >= 0.0)

    # Map expected bin to fftshifted index.
    # When nfft=np_chirps*2, bin scaling is by factor 2.
    scale = nfft / np_chirps
    center = nfft // 2
    for rng_bin, dop_bin in expected.items():
        expected_idx = int(round(center + dop_bin * scale))
        actual_idx = int(np.argmax(fx[:, rng_bin]))
        actual_idx_w = int(np.argmax(fx_win[:, rng_bin]))
        assert abs(actual_idx - expected_idx) <= 1, (rng_bin, actual_idx, expected_idx)
        assert abs(actual_idx_w - expected_idx) <= 1, (rng_bin, actual_idx_w, expected_idx)

    print("Hybrid Doppler estimation replacement validation passed.")


if __name__ == "__main__":
    run()

