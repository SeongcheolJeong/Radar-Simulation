#!/usr/bin/env python3
import numpy as np

from avxsim.hybrid_pcode import generate_channel_from_distances, run_hybrid_estimation_bundle


def run() -> None:
    num_tx = 2
    num_rx = 3
    n_points = 6
    n_frames = 4
    np_chirps = 8
    ns = 64
    nfft = 96

    f0_hz = 77e9
    c_mps = 299_792_458.0
    bw_hz = 3.6e9
    chirp_duration_s = 6e-5
    slow_time_delta_t = 0.04
    frame_step_for_velo = 1
    t_slow = np.arange(np_chirps, dtype=np.float64) * 2e-4
    t_fast = np.arange(ns, dtype=np.float64) / 10e6
    frame_idx = 1

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

    h, _, _ = generate_channel_from_distances(
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

    out = run_hybrid_estimation_bundle(
        h=h,
        np_chirps=np_chirps,
        ns=ns,
        nfft=nfft,
        num_tx=num_tx,
        num_rx=num_rx,
        angle_view_cali=(-45.0, 45.0),
        range_bin_length=10,
    )

    assert out["fx_dop"].shape == (nfft, ns)
    assert out["fx_dop_win"].shape == (nfft, ns)
    assert out["fx_dop_max"].shape == (nfft, 1)
    assert out["fx_dop_ave"].shape == (nfft, 1)
    assert out["fx_ang"].shape == (nfft, ns)
    assert out["cap_range_azimuth"].shape == (ns, num_tx * num_rx)
    assert out["ncap"] == num_tx * num_rx

    for key in ("fx_dop", "fx_dop_win", "fx_dop_max", "fx_dop_ave", "fx_ang", "cap_range_azimuth"):
        assert np.all(np.isfinite(out[key]))

    print("Hybrid P-code bundle validation passed.")


if __name__ == "__main__":
    run()

