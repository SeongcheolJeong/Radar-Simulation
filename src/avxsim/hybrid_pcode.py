from typing import Optional, Sequence, Tuple

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


def doppler_estimation_from_channel(
    h: np.ndarray,
    np_chirps: int,
    nfft: int,
    window: str = "hann",
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Python replacement candidate for fun_hybrid_Doppler_estimation.

    Input:
      h: complex channel matrix with shape (n_virtual*np_chirps, n_range_bins)
      np_chirps: chirps per CPI
      nfft: Doppler FFT size

    Output:
      fx_dop:     shape (nfft, n_range_bins), power map
      fx_dop_win: shape (nfft, n_range_bins), power map with slow-time window
    """
    h_arr = np.asarray(h)
    if h_arr.ndim != 2:
        raise ValueError("h must be 2D with shape (n_virtual*np_chirps, n_range_bins)")
    if np_chirps <= 0:
        raise ValueError("np_chirps must be positive")
    if nfft <= 0:
        raise ValueError("nfft must be positive")
    if h_arr.shape[0] % np_chirps != 0:
        raise ValueError("h first dimension must be divisible by np_chirps")

    n_virtual = h_arr.shape[0] // np_chirps
    n_range = h_arr.shape[1]
    cube = h_arr.reshape(n_virtual, np_chirps, n_range)

    fx_dop = _doppler_power_map(cube, nfft=nfft, slow_window=None)
    slow_window = _get_slow_time_window(np_chirps, window=window)
    fx_dop_win = _doppler_power_map(cube, nfft=nfft, slow_window=slow_window)
    return fx_dop, fx_dop_win


def generate_concatenated_doppler(
    fx_dop: np.ndarray,
    range_bin_length: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Python replacement candidate for fun_hybrid_generate_concatenated_Dop.

    Input:
      fx_dop: Doppler-range power map, shape (nfft, n_range_bins)
      range_bin_length: aggregation width around dominant range bin

    Output:
      fx_dop_max: (nfft, 1) max over selected range window
      fx_dop_ave: (nfft, 1) mean over selected range window
    """
    dop = np.asarray(fx_dop, dtype=np.float64)
    if dop.ndim != 2:
        raise ValueError("fx_dop must be 2D with shape (nfft, n_range_bins)")
    if range_bin_length <= 0:
        raise ValueError("range_bin_length must be positive")

    _, n_range = dop.shape
    power_by_range = np.sum(dop, axis=0)
    center = int(np.argmax(power_by_range))
    half = int(range_bin_length // 2)
    start = max(0, center - half)
    end = min(n_range, start + int(range_bin_length))
    start = max(0, end - int(range_bin_length))
    sel = dop[:, start:end]
    if sel.shape[1] == 0:
        raise ValueError("empty range selection in concatenated Doppler")

    fx_dop_max = np.max(sel, axis=1, keepdims=True)
    fx_dop_ave = np.mean(sel, axis=1, keepdims=True)
    return fx_dop_max, fx_dop_ave


def angle_estimation_from_channel(
    h: np.ndarray,
    np_chirps: int,
    ns: int,
    nfft: int,
    num_tx: int,
    num_rx: int,
    angle_view_cali: Sequence[float],
) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Python replacement candidate for fun_hybrid_Ang_estimation.

    Input:
      h: complex channel matrix with shape (num_tx*num_rx*np_chirps, ns)

    Output:
      fx_ang: (nfft, ns) range-angle power map
      cap_range_azimuth: (ns, ncap) coarse map over virtual channels
      ncap: number of coarse angle bins
    """
    _ = angle_view_cali  # axis calibration is used by caller for plotting.
    h_arr = np.asarray(h)
    if h_arr.ndim != 2:
        raise ValueError("h must be 2D")
    if ns <= 0 or nfft <= 0:
        raise ValueError("ns and nfft must be positive")
    if np_chirps <= 0:
        raise ValueError("np_chirps must be positive")
    if num_tx <= 0 or num_rx <= 0:
        raise ValueError("num_tx and num_rx must be positive")
    n_virtual = int(num_tx) * int(num_rx)
    if h_arr.shape[0] != n_virtual * int(np_chirps):
        raise ValueError("h first dimension must be num_tx*num_rx*np_chirps")
    if h_arr.shape[1] != int(ns):
        raise ValueError("h second dimension must equal ns")

    cube = h_arr.reshape(n_virtual, int(np_chirps), int(ns))
    # Coherent integration over chirps to form per-range spatial snapshots.
    snapshots = np.mean(cube, axis=1)  # (n_virtual, ns)

    # Fine angle grid
    spec_fine = np.fft.fftshift(np.fft.fft(snapshots, n=int(nfft), axis=0), axes=0)
    fx_ang = np.maximum(np.abs(spec_fine) ** 2, np.finfo(np.float64).tiny)

    # Coarse grid equal to virtual array size
    spec_coarse = np.fft.fftshift(np.fft.fft(snapshots, axis=0), axes=0)
    cap_range_azimuth = np.maximum(np.abs(spec_coarse).T, np.finfo(np.float64).tiny)
    ncap = n_virtual
    return fx_ang, cap_range_azimuth, int(ncap)


def calculate_reflecting_path_power(
    p_t_dbm: float,
    pixel_width: int,
    pixel_height: int,
    reflecting_coefficient: float,
    lambda_m: float,
    temp_range_m: np.ndarray,
    range_power_exponent: float = 4.0,
    gain_scale: float = 1.0,
    epsilon: float = 1e-6,
) -> np.ndarray:
    """
    Python replacement candidate for fun_hybrid_calculate_reflecting_path_power.

    Returns linear amplitude-like weights per path/pixel.
    """
    if pixel_width <= 0 or pixel_height <= 0:
        raise ValueError("pixel dimensions must be positive")
    if lambda_m <= 0:
        raise ValueError("lambda_m must be positive")
    if range_power_exponent <= 0:
        raise ValueError("range_power_exponent must be positive")
    if gain_scale < 0:
        raise ValueError("gain_scale must be non-negative")

    r = np.maximum(np.asarray(temp_range_m, dtype=np.float64).reshape(-1), float(epsilon))
    n_pix = float(pixel_width * pixel_height)
    p_t_w = _dbm_to_w(float(p_t_dbm))
    coeff = max(0.0, float(reflecting_coefficient))

    # Monostatic radar-equation style scaling with configurable range power law.
    power = (
        float(gain_scale)
        * (p_t_w * coeff * (lambda_m**2))
        / (((4.0 * np.pi) ** 3) * (r ** float(range_power_exponent)))
    )
    power /= max(n_pix, 1.0)
    return np.sqrt(np.maximum(power, 0.0))


def calculate_scattering_path_power(
    p_t_dbm: float,
    pixel_width: int,
    pixel_height: int,
    scattering_coefficient: float,
    lambda_m: float,
    temp_range_m: np.ndarray,
    temp_angles_rad: np.ndarray,
    range_power_exponent: float = 4.0,
    gain_scale: float = 1.0,
    elevation_power: float = 2.0,
    azimuth_mix: float = 0.6,
    azimuth_power: float = 2.0,
    epsilon: float = 1e-6,
) -> np.ndarray:
    """
    Python replacement candidate for fun_hybrid_calculate_scattering_path_power.

    Applies a diffuse-like angular term over the reflecting baseline.
    """
    base = calculate_reflecting_path_power(
        p_t_dbm=p_t_dbm,
        pixel_width=pixel_width,
        pixel_height=pixel_height,
        reflecting_coefficient=scattering_coefficient,
        lambda_m=lambda_m,
        temp_range_m=temp_range_m,
        range_power_exponent=range_power_exponent,
        gain_scale=gain_scale,
        epsilon=epsilon,
    )

    ang = np.asarray(temp_angles_rad, dtype=np.float64)
    if ang.ndim != 2 or ang.shape[1] < 2:
        raise ValueError("temp_angles_rad must have shape (N, >=2) with [az, el]")
    if ang.shape[0] != base.shape[0]:
        raise ValueError("angle rows must match range vector length")
    if elevation_power < 0:
        raise ValueError("elevation_power must be non-negative")
    if azimuth_power < 0:
        raise ValueError("azimuth_power must be non-negative")
    if azimuth_mix < 0 or azimuth_mix > 1:
        raise ValueError("azimuth_mix must be in [0, 1]")

    # Diffuse-like directional attenuation.
    az = ang[:, 0]
    el = ang[:, 1]
    el_term = np.maximum(np.cos(el), 0.0) ** float(elevation_power)
    az_term = float(azimuth_mix) + (1.0 - float(azimuth_mix)) * (
        np.abs(np.cos(az)) ** float(azimuth_power)
    )
    directional = el_term * az_term
    return base * directional


def run_hybrid_estimation_bundle(
    h: np.ndarray,
    np_chirps: int,
    ns: int,
    nfft: int,
    num_tx: int,
    num_rx: int,
    angle_view_cali: Sequence[float],
    range_bin_length: int,
    doppler_window: str = "hann",
    h_for_angle: Optional[np.ndarray] = None,
) -> dict:
    """
    Integrated compatibility path for HybridDynamicRT post-processing.
    """
    fx_dop, fx_dop_win = doppler_estimation_from_channel(
        h=h,
        np_chirps=np_chirps,
        nfft=nfft,
        window=doppler_window,
    )
    fx_dop_max, fx_dop_ave = generate_concatenated_doppler(
        fx_dop=fx_dop,
        range_bin_length=range_bin_length,
    )
    fx_dop_max_win, fx_dop_ave_win = generate_concatenated_doppler(
        fx_dop=fx_dop_win,
        range_bin_length=range_bin_length,
    )
    h_ang = h if h_for_angle is None else np.asarray(h_for_angle)
    fx_ang, cap_range_azimuth, ncap = angle_estimation_from_channel(
        h=h_ang,
        np_chirps=np_chirps,
        ns=ns,
        nfft=nfft,
        num_tx=num_tx,
        num_rx=num_rx,
        angle_view_cali=angle_view_cali,
    )
    return {
        "fx_dop": fx_dop,
        "fx_dop_win": fx_dop_win,
        "fx_dop_max": fx_dop_max,
        "fx_dop_ave": fx_dop_ave,
        "fx_dop_max_win": fx_dop_max_win,
        "fx_dop_ave_win": fx_dop_ave_win,
        "fx_ang": fx_ang,
        "cap_range_azimuth": cap_range_azimuth,
        "ncap": ncap,
    }


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


def _doppler_power_map(
    cube: np.ndarray,
    nfft: int,
    slow_window: np.ndarray,
) -> np.ndarray:
    # cube: (n_virtual, np_chirps, n_range)
    if slow_window is not None:
        cube = cube * slow_window[None, :, None]

    dop = np.fft.fftshift(np.fft.fft(cube, n=nfft, axis=1), axes=1)
    power = np.sum(np.abs(dop) ** 2, axis=0)
    power = np.real(power)
    # Avoid exact zeros in downstream log-scale visualization.
    return np.maximum(power, np.finfo(np.float64).tiny)


def _get_slow_time_window(np_chirps: int, window: str) -> np.ndarray:
    name = str(window).lower()
    if name in {"hann", "hanning"}:
        return np.hanning(np_chirps).astype(np.float64)
    if name in {"hamming"}:
        return np.hamming(np_chirps).astype(np.float64)
    if name in {"rect", "rectangular", "none"}:
        return np.ones(np_chirps, dtype=np.float64)
    raise ValueError(f"unsupported window type: {window}")


def _dbm_to_w(p_dbm: float) -> float:
    return 10.0 ** ((p_dbm - 30.0) / 10.0)


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
