from typing import Sequence, Tuple

import numpy as np


def generate_channel_from_distances(
    num_tx: int,
    num_rx: int,
    distan_all_array: object,
    frame_index: int,
    target_move_m: np.ndarray,
    slow_time_delta_t: float,
    frame_step_for_velo: int,
    removed_indices: Sequence[int],
    t_slow: np.ndarray,
    temp_s: np.ndarray,
    f0_hz: float,
    c_mps: float,
    np_chirps: int,
    bw_hz: float,
    chirp_duration_s: float,
    t_fast: np.ndarray,
    frame_index_is_one_based: bool = False,
) -> Tuple[np.ndarray, float, float]:
    """
    Python equivalent of HybridDynamicRT's fun_hybrid_generate_channel.

    Output:
      H: (num_tx * num_rx * np_chirps, n_fast) complex128
      dop_mean: scalar
      dop_spread: scalar
    """
    if num_tx <= 0 or num_rx <= 0:
        raise ValueError("num_tx and num_rx must be positive")
    if np_chirps <= 0:
        raise ValueError("np_chirps must be positive")
    if frame_step_for_velo <= 0:
        raise ValueError("frame_step_for_velo must be positive")
    if slow_time_delta_t <= 0:
        raise ValueError("slow_time_delta_t must be positive")
    if chirp_duration_s <= 0:
        raise ValueError("chirp_duration_s must be positive")
    if c_mps <= 0:
        raise ValueError("c_mps must be positive")

    frame_idx = int(frame_index) - 1 if frame_index_is_one_based else int(frame_index)
    if frame_idx < 0:
        raise ValueError("frame_index resolves to negative value")

    t_slow_arr = np.asarray(t_slow, dtype=np.float64).reshape(-1)
    t_fast_arr = np.asarray(t_fast, dtype=np.float64).reshape(-1)
    if t_slow_arr.size != np_chirps:
        raise ValueError("len(t_slow) must match np_chirps")
    if t_fast_arr.size == 0:
        raise ValueError("t_fast must be non-empty")

    target_move = np.asarray(target_move_m, dtype=np.float64).reshape(-1)
    removed = np.asarray(list(removed_indices), dtype=np.int64).reshape(-1)
    removed = np.unique(removed[removed >= 0])

    v_full = (-1.0 * target_move) / (2.0 * float(slow_time_delta_t) * float(frame_step_for_velo))
    v_filtered = np.delete(v_full, removed) if removed.size > 0 else v_full

    temp_s_arr = np.asarray(temp_s).reshape(-1)
    if temp_s_arr.size == v_filtered.size:
        temp_s_filtered = temp_s_arr
    elif temp_s_arr.size == v_full.size:
        temp_s_filtered = np.delete(temp_s_arr, removed) if removed.size > 0 else temp_s_arr
    else:
        raise ValueError("temp_s length must match filtered or full velocity vector length")

    h_rows = []
    for tx_idx in range(num_tx):
        for rx_idx in range(num_rx):
            dist_vec = _extract_distance_vector(
                distan_all_array=distan_all_array,
                tx_idx=tx_idx,
                rx_idx=rx_idx,
                frame_idx=frame_idx,
            )
            range_full = dist_vec / 2.0
            if range_full.size == v_full.size:
                temp_range = np.delete(range_full, removed) if removed.size > 0 else range_full
            elif range_full.size == v_filtered.size:
                temp_range = range_full
            else:
                raise ValueError("distance vector length mismatch against velocity vectors")

            h_pair = _build_h_matrix(
                temp_v=v_filtered,
                temp_range=temp_range,
                temp_s=temp_s_filtered,
                t_slow=t_slow_arr,
                t_fast=t_fast_arr,
                f0_hz=float(f0_hz),
                c_mps=float(c_mps),
                np_chirps=int(np_chirps),
                bw_hz=float(bw_hz),
                chirp_duration_s=float(chirp_duration_s),
            )
            h_rows.append(np.fft.fft(h_pair, axis=1))

    h_out = np.vstack(h_rows)

    weights = np.asarray(temp_s_filtered) ** 2
    if np.sum(weights) == 0:
        raise ValueError("sum(temp_s^2) must be non-zero")
    dop_mean = np.sum(weights * (-2.0 * v_filtered)) / np.sum(weights)
    dop_2nd = np.sum(weights * ((-2.0 * v_filtered) ** 2)) / np.sum(weights)
    dop_spread = np.sqrt(dop_2nd - dop_mean**2)
    return h_out, float(np.real(dop_mean)), float(np.real(dop_spread))


def _build_h_matrix(
    temp_v: np.ndarray,
    temp_range: np.ndarray,
    temp_s: np.ndarray,
    t_slow: np.ndarray,
    t_fast: np.ndarray,
    f0_hz: float,
    c_mps: float,
    np_chirps: int,
    bw_hz: float,
    chirp_duration_s: float,
) -> np.ndarray:
    if temp_range.size != temp_v.size or temp_range.size != temp_s.size:
        raise ValueError("temp_range, temp_v, temp_s must have matching sizes")

    # Slow-time modulation: shape (Np, Npaths)
    slow_phase = np.exp(
        1j * 2.0 * np.pi * (-2.0) * (np.outer(temp_v, t_slow) * f0_hz / c_mps)
    ).T
    amp_phase = temp_s * np.exp(1j * 2.0 * np.pi * (2.0 * temp_range * f0_hz / c_mps))
    slow_weighted = slow_phase * np.tile(amp_phase[None, :], (np_chirps, 1))

    # Fast-time modulation: shape (Npaths, Ns)
    fast_phase = np.exp(
        1j
        * 2.0
        * np.pi
        * (
            (2.0 * temp_range[:, None] * bw_hz / chirp_duration_s / c_mps)
            * t_fast[None, :]
        )
    )
    return slow_weighted @ fast_phase


def _extract_distance_vector(
    distan_all_array: object,
    tx_idx: int,
    rx_idx: int,
    frame_idx: int,
) -> np.ndarray:
    if isinstance(distan_all_array, np.ndarray):
        if distan_all_array.dtype == object and distan_all_array.ndim == 2:
            cell = distan_all_array[tx_idx, rx_idx]
            return _slice_cell_frame(cell, frame_idx)
        if distan_all_array.ndim == 4:
            return np.asarray(distan_all_array[tx_idx, rx_idx, :, frame_idx], dtype=np.float64)

    # MATLAB cell-array style mapped into nested Python lists
    try:
        cell = distan_all_array[tx_idx][rx_idx]
    except Exception as exc:
        raise ValueError("unsupported distan_all_array structure") from exc
    return _slice_cell_frame(cell, frame_idx)


def _slice_cell_frame(cell: object, frame_idx: int) -> np.ndarray:
    arr = np.asarray(cell, dtype=np.float64)
    if arr.ndim == 1:
        return arr
    if arr.ndim == 2:
        if frame_idx >= arr.shape[1]:
            raise IndexError(
                f"frame index {frame_idx} out of range for distance matrix with {arr.shape[1]} frames"
            )
        return np.asarray(arr[:, frame_idx], dtype=np.float64)
    raise ValueError(f"unsupported cell data shape: {arr.shape}")

