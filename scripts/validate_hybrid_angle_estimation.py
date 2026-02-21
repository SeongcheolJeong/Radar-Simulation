#!/usr/bin/env python3
import numpy as np

from avxsim.hybrid_pcode import angle_estimation_from_channel


def _build_h_with_known_spatial_bin(
    num_tx: int,
    num_rx: int,
    np_chirps: int,
    ns: int,
    range_bin: int,
    spatial_bin: int,
) -> np.ndarray:
    n_virtual = num_tx * num_rx
    snapshots = np.zeros((n_virtual, ns), dtype=np.complex128)
    v = np.arange(n_virtual, dtype=np.float64)
    snapshots[:, range_bin] = np.exp(1j * 2.0 * np.pi * spatial_bin * v / n_virtual)

    cube = np.zeros((n_virtual, np_chirps, ns), dtype=np.complex128)
    for k in range(np_chirps):
        cube[:, k, :] = snapshots
    return cube.reshape(n_virtual * np_chirps, ns)


def run() -> None:
    num_tx = 2
    num_rx = 4
    np_chirps = 16
    ns = 96
    nfft = 128
    n_virtual = num_tx * num_rx

    range_bin = 37
    spatial_bin = 2
    h = _build_h_with_known_spatial_bin(
        num_tx=num_tx,
        num_rx=num_rx,
        np_chirps=np_chirps,
        ns=ns,
        range_bin=range_bin,
        spatial_bin=spatial_bin,
    )

    fx_ang, cap, ncap = angle_estimation_from_channel(
        h=h,
        np_chirps=np_chirps,
        ns=ns,
        nfft=nfft,
        num_tx=num_tx,
        num_rx=num_rx,
        angle_view_cali=(-45.0, 45.0),
    )

    assert fx_ang.shape == (nfft, ns), fx_ang.shape
    assert cap.shape == (ns, n_virtual), cap.shape
    assert ncap == n_virtual
    assert np.all(fx_ang >= 0.0)
    assert np.all(cap >= 0.0)

    expected_fine = int(round((nfft // 2) + spatial_bin * (nfft / n_virtual)))
    peak_fine = int(np.argmax(fx_ang[:, range_bin]))
    assert abs(peak_fine - expected_fine) <= 1, (peak_fine, expected_fine)

    expected_coarse = (n_virtual // 2) + spatial_bin
    peak_coarse = int(np.argmax(cap[range_bin, :]))
    assert peak_coarse == expected_coarse, (peak_coarse, expected_coarse)

    print("Hybrid angle estimation replacement validation passed.")


if __name__ == "__main__":
    run()

