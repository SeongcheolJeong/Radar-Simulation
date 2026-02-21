#!/usr/bin/env python3
import numpy as np

from avxsim.hybrid_pcode import generate_channel_from_distances


def _reference_generate_channel(
    num_tx: int,
    num_rx: int,
    distan_all_array: list,
    frame_idx: int,
    target_move: np.ndarray,
    slow_time_delta_t: float,
    frame_step_for_velo: int,
    removed_indices: np.ndarray,
    t_slow: np.ndarray,
    temp_s_filtered: np.ndarray,
    f0_hz: float,
    c_mps: float,
    np_chirps: int,
    bw_hz: float,
    chirp_duration_s: float,
    t_fast: np.ndarray,
):
    v_full = (-1.0 * target_move) / (2.0 * slow_time_delta_t * frame_step_for_velo)
    v = np.delete(v_full, removed_indices)

    out = []
    for tx in range(num_tx):
        for rx in range(num_rx):
            temp_range = np.delete(distan_all_array[tx][rx][:, frame_idx] / 2.0, removed_indices)

            slow_phase = np.exp(
                1j * 2.0 * np.pi * (-2.0) * (np.outer(v, t_slow) * f0_hz / c_mps)
            ).T
            amp_phase = temp_s_filtered * np.exp(1j * 2.0 * np.pi * (2.0 * temp_range * f0_hz / c_mps))
            fast_phase = np.exp(
                1j
                * 2.0
                * np.pi
                * ((2.0 * temp_range[:, None] * bw_hz / chirp_duration_s / c_mps) * t_fast[None, :])
            )
            h = np.einsum("pn,ns->ps", slow_phase * amp_phase[None, :], fast_phase)
            out.append(np.fft.fft(h, axis=1))

    h_ref = np.vstack(out)
    w = temp_s_filtered**2
    dop_mean = np.sum(w * (-2.0 * v)) / np.sum(w)
    dop_2nd = np.sum(w * ((-2.0 * v) ** 2)) / np.sum(w)
    dop_spread = np.sqrt(dop_2nd - dop_mean**2)
    return h_ref, float(np.real(dop_mean)), float(np.real(dop_spread))


def run() -> None:
    num_tx = 2
    num_rx = 3
    n_points = 6
    n_frames = 4
    np_chirps = 8
    ns = 64

    f0_hz = 77e9
    c_mps = 299_792_458.0
    bw_hz = 3.6e9
    chirp_duration_s = 6e-5
    slow_time_delta_t = 0.04
    frame_step_for_velo = 1
    t_slow = np.arange(np_chirps, dtype=np.float64) * 2e-4
    t_fast = np.arange(ns, dtype=np.float64) / 10e6
    frame_idx = 1

    # Build synthetic distance matrices: each pair has a slightly shifted base.
    distan_all_array = []
    base_points = np.linspace(8.0, 14.0, n_points)
    for tx in range(num_tx):
        row = []
        for rx in range(num_rx):
            pair_offset = 0.1 * (tx * num_rx + rx)
            mat = np.zeros((n_points, n_frames), dtype=np.float64)
            for fi in range(n_frames):
                mat[:, fi] = base_points + pair_offset + 0.02 * fi
            row.append(mat)
        distan_all_array.append(row)

    target_move = np.array([0.015, -0.010, 0.002, 0.006, -0.012, 0.003], dtype=np.float64)
    removed = np.array([1, 4], dtype=np.int64)
    temp_s_full = np.array([1.0, 0.85, 0.9, 0.75, 0.65, 0.8], dtype=np.float64)
    temp_s_filtered = np.delete(temp_s_full, removed)

    h_py, dop_mean_py, dop_spread_py = generate_channel_from_distances(
        num_tx=num_tx,
        num_rx=num_rx,
        distan_all_array=distan_all_array,
        frame_index=frame_idx,
        target_move_m=target_move,
        slow_time_delta_t=slow_time_delta_t,
        frame_step_for_velo=frame_step_for_velo,
        removed_indices=removed,
        t_slow=t_slow,
        temp_s=temp_s_filtered,
        f0_hz=f0_hz,
        c_mps=c_mps,
        np_chirps=np_chirps,
        bw_hz=bw_hz,
        chirp_duration_s=chirp_duration_s,
        t_fast=t_fast,
        frame_index_is_one_based=False,
    )

    h_ref, dop_mean_ref, dop_spread_ref = _reference_generate_channel(
        num_tx=num_tx,
        num_rx=num_rx,
        distan_all_array=distan_all_array,
        frame_idx=frame_idx,
        target_move=target_move,
        slow_time_delta_t=slow_time_delta_t,
        frame_step_for_velo=frame_step_for_velo,
        removed_indices=removed,
        t_slow=t_slow,
        temp_s_filtered=temp_s_filtered,
        f0_hz=f0_hz,
        c_mps=c_mps,
        np_chirps=np_chirps,
        bw_hz=bw_hz,
        chirp_duration_s=chirp_duration_s,
        t_fast=t_fast,
    )

    assert h_py.shape == (num_tx * num_rx * np_chirps, ns), h_py.shape
    assert np.allclose(h_py, h_ref, atol=1e-10, rtol=1e-10)
    assert abs(dop_mean_py - dop_mean_ref) < 1e-12
    assert abs(dop_spread_py - dop_spread_ref) < 1e-12
    print("Hybrid generate_channel replacement validation passed.")


if __name__ == "__main__":
    run()
