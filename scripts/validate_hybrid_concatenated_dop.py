#!/usr/bin/env python3
import numpy as np

from avxsim.hybrid_pcode import generate_concatenated_doppler


def run() -> None:
    nfft = 64
    n_range = 80
    fx = np.zeros((nfft, n_range), dtype=np.float64)

    # Inject dominant cluster around range bin 30
    center = 30
    for r in range(center - 2, center + 3):
        fx[:, r] += np.exp(-((np.arange(nfft) - 20) ** 2) / (2 * 4.0**2))

    range_bin_length = 10
    fx_max, fx_ave = generate_concatenated_doppler(fx, range_bin_length=range_bin_length)

    assert fx_max.shape == (nfft, 1), fx_max.shape
    assert fx_ave.shape == (nfft, 1), fx_ave.shape
    assert np.all(fx_max >= fx_ave)

    power_by_range = np.sum(fx, axis=0)
    chosen_center = int(np.argmax(power_by_range))
    assert 28 <= chosen_center <= 32, chosen_center

    half = range_bin_length // 2
    start = max(0, chosen_center - half)
    end = min(n_range, start + range_bin_length)
    start = max(0, end - range_bin_length)
    expected = fx[:, start:end]
    assert np.allclose(fx_max[:, 0], np.max(expected, axis=1))
    assert np.allclose(fx_ave[:, 0], np.mean(expected, axis=1))

    print("Hybrid concatenated Doppler replacement validation passed.")


if __name__ == "__main__":
    run()
