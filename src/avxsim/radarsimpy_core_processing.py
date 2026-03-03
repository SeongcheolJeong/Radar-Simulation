from __future__ import annotations

from typing import Any
from warnings import warn

import numpy as np
from scipy import linalg
from scipy.signal import convolve, find_peaks


def _normalize_axis(axis: int, ndim: int) -> int:
    if ndim <= 0:
        raise ValueError("array must have at least one dimension")
    a = int(axis)
    if a < 0:
        a += ndim
    if a < 0 or a >= ndim:
        raise ValueError(f"axis out of range: axis={axis}, ndim={ndim}")
    return a


def _as_pair(v: Any) -> tuple[int, int]:
    x = np.asarray(v)
    if x.size == 1:
        i = int(x.item())
        return i, i
    flat = x.flatten()
    if flat.size != 2:
        raise ValueError("expected scalar or length-2 value")
    return int(flat[0]), int(flat[1])


def _log_factorial(n: int | np.ndarray) -> float | np.ndarray:
    if np.isscalar(n):
        ni = int(n)
        if ni <= 1:
            return 0.0
        return float(np.sum(np.log(np.arange(1, ni + 1, dtype=np.float64))))
    arr = np.asarray(n, dtype=np.int64)
    out = np.zeros_like(arr, dtype=np.float64)
    it = np.nditer(arr, flags=["multi_index"])
    while not it.finished:
        v = int(it[0])
        if v <= 1:
            out[it.multi_index] = 0.0
        else:
            out[it.multi_index] = float(np.sum(np.log(np.arange(1, v + 1, dtype=np.float64))))
        it.iternext()
    return out


def _os_cfar_threshold(k: int, n: int, pfa: float) -> float:
    def _fun(kk: int, nn: int, t_os: float, p: float) -> float:
        return float(
            _log_factorial(nn)
            - _log_factorial(nn - kk)
            - np.sum(np.log(np.arange(nn, nn - kk, -1, dtype=np.float64) + t_os))
            - np.log(p)
        )

    t_max = 1e32
    t_min = 1.0
    max_iter = 10000
    for _ in range(max_iter):
        f_tmin = _fun(k, n, t_min, pfa)
        f_tmax = _fun(k, n, t_max, pfa)
        den = f_tmin - f_tmax
        if den == 0:
            break
        m_n = t_max - f_tmax * (t_min - t_max) / den
        f_m_n = _fun(k, n, m_n, pfa)
        if f_m_n == 0 or abs(f_m_n) < 1e-4:
            return float(m_n)
        if f_tmax * f_m_n < 0:
            t_min = float(m_n)
        elif f_tmin * f_m_n < 0:
            t_max = float(m_n)
        else:
            break
    raise RuntimeError("failed to compute OS-CFAR threshold")


def _apply_window(x: np.ndarray, *, axis: int, window: Any | None) -> np.ndarray:
    if window is None:
        return x
    w = np.asarray(window)
    if w.ndim != 1:
        raise ValueError("window must be 1-D")
    if w.shape[0] != x.shape[axis]:
        raise ValueError(
            f"window length mismatch: window={w.shape[0]}, axis_size={x.shape[axis]}"
        )
    shape = [1] * x.ndim
    shape[axis] = w.shape[0]
    return x * w.reshape(shape)


def _steering_vector(
    n_array: int,
    spacing: float,
    scanangles: Any = range(-90, 91),
) -> tuple[np.ndarray, np.ndarray]:
    scan = np.asarray(scanangles, dtype=np.float64)
    arr = np.linspace(0, (n_array - 1) * float(spacing), n_array, dtype=np.float64)
    arr_grid, ang_grid = np.meshgrid(arr, np.radians(scan), indexing="ij")
    sv = np.exp(1j * 2 * np.pi * arr_grid * np.sin(ang_grid)) / np.sqrt(float(n_array))
    return scan, sv


def core_range_fft(
    data: Any,
    *,
    axis: int = -1,
    n: int | None = None,
    window: Any | None = None,
) -> np.ndarray:
    x = np.asarray(data)
    a = _normalize_axis(axis, x.ndim)
    y = _apply_window(x, axis=a, window=window)
    return np.fft.fft(y, n=n, axis=a)


def core_doppler_fft(
    data: Any,
    *,
    axis: int = -2,
    n: int | None = None,
    window: Any | None = None,
) -> np.ndarray:
    x = np.asarray(data)
    a = _normalize_axis(axis, x.ndim)
    y = _apply_window(x, axis=a, window=window)
    return np.fft.fft(y, n=n, axis=a)


def core_range_doppler_fft(
    data: Any,
    *,
    range_axis: int = -1,
    doppler_axis: int = -2,
    range_n: int | None = None,
    doppler_n: int | None = None,
    range_window: Any | None = None,
    doppler_window: Any | None = None,
) -> np.ndarray:
    x = np.asarray(data)
    r = core_range_fft(
        x,
        axis=range_axis,
        n=range_n,
        window=range_window,
    )
    d = core_doppler_fft(
        r,
        axis=doppler_axis,
        n=doppler_n,
        window=doppler_window,
    )
    return d


def core_cfar_ca_1d(
    data: Any,
    guard: int,
    trailing: int,
    pfa: float = 1e-5,
    axis: int = 0,
    detector: str = "squarelaw",
    offset: float | None = None,
) -> np.ndarray:
    x = np.asarray(data)
    if np.iscomplexobj(x):
        raise ValueError("Input data should not be complex.")
    if int(trailing) <= 0:
        raise ValueError("trailing must be > 0")
    if offset is None:
        if detector == "squarelaw":
            a = float(trailing * 2 * (float(pfa) ** (-1.0 / (float(trailing) * 2.0)) - 1.0))
        elif detector == "linear":
            a = float(np.sqrt(trailing * 2 * (float(pfa) ** (-1.0 / (float(trailing) * 2.0)) - 1.0)))
        else:
            raise ValueError("`detector` can only be `linear` or `squarelaw`.")
    else:
        a = float(offset)

    cfar_win = np.ones((int(guard) + int(trailing)) * 2 + 1, dtype=np.float64)
    cfar_win[int(trailing) : (int(trailing) + int(guard) * 2 + 1)] = 0.0
    cfar_win = cfar_win / np.sum(cfar_win)

    ax = _normalize_axis(axis, x.ndim)

    def _conv(v: np.ndarray) -> np.ndarray:
        return a * convolve(v, cfar_win, mode="same")

    return np.apply_along_axis(_conv, ax, x)


def core_cfar_ca_2d(
    data: Any,
    guard: int | tuple[int, int] | list[int] | np.ndarray,
    trailing: int | tuple[int, int] | list[int] | np.ndarray,
    pfa: float = 1e-5,
    detector: str = "squarelaw",
    offset: float | None = None,
) -> np.ndarray:
    x = np.asarray(data)
    if x.ndim != 2:
        raise ValueError("cfar_ca_2d expects 2-D data")
    if np.iscomplexobj(x):
        raise ValueError("Input data should not be complex.")

    g0, g1 = _as_pair(guard)
    t0, t1 = _as_pair(trailing)
    tg0 = t0 + g0
    tg1 = t1 + g1
    t_num = (2 * tg0 + 1) * (2 * tg1 + 1)
    g_num = (2 * g0 + 1) * (2 * g1 + 1)
    n_train = t_num - g_num
    if n_train <= 0:
        raise ValueError("No trailing bins!")

    if offset is None:
        if detector == "squarelaw":
            a = float(n_train * (float(pfa) ** (-1.0 / float(n_train)) - 1.0))
        elif detector == "linear":
            a = float(np.sqrt(n_train * (float(pfa) ** (-1.0 / float(n_train)) - 1.0)))
        else:
            raise ValueError("`detector` can only be `linear` or `squarelaw`.")
    else:
        a = float(offset)

    cfar_win = np.ones((2 * tg0 + 1, 2 * tg1 + 1), dtype=np.float64)
    cfar_win[t0 : (t0 + 2 * g0 + 1), t1 : (t1 + 2 * g1 + 1)] = 0.0
    cfar_win = cfar_win / np.sum(cfar_win)
    return a * convolve(x, cfar_win, mode="same")


def core_cfar_os_1d(
    data: Any,
    guard: int,
    trailing: int,
    k: int,
    pfa: float = 1e-5,
    axis: int = 0,
    detector: str = "squarelaw",
    offset: float | None = None,
) -> np.ndarray:
    x = np.asarray(data)
    if np.iscomplexobj(x):
        raise ValueError("Input data should not be complex.")
    guard_i = int(guard)
    trailing_i = int(trailing)
    k_i = int(k)
    if trailing_i <= 0:
        raise ValueError("trailing must be > 0")
    n_train = trailing_i * 2
    if offset is None:
        if detector == "squarelaw":
            a = float(_os_cfar_threshold(k_i, n_train, float(pfa)))
        elif detector == "linear":
            a = float(np.sqrt(_os_cfar_threshold(k_i, n_train, float(pfa))))
        else:
            raise ValueError("`detector` can only be `linear` or `squarelaw`.")
    else:
        a = float(offset)

    if k_i < trailing_i or k_i > (trailing_i * 2):
        warn(
            f"k is usually in (N/2, N), N={trailing_i * 2}; typical k~0.75N",
            RuntimeWarning,
        )
    if k_i < 0 or k_i >= n_train:
        raise ValueError("k out of range for ordered statistics training bins")

    def _os(v: np.ndarray) -> np.ndarray:
        n = int(v.shape[0])
        out = np.zeros_like(v, dtype=np.float64)
        for idx in range(n):
            win_idx = np.mod(
                np.concatenate(
                    [
                        np.arange(idx - trailing_i - guard_i, idx - guard_i, 1),
                        np.arange(idx + 1 + guard_i, idx + 1 + trailing_i + guard_i, 1),
                    ]
                ),
                n,
            ).astype(np.int64)
            samples = np.sort(v[win_idx])
            out[idx] = a * samples[k_i]
        return out

    ax = _normalize_axis(axis, x.ndim)
    return np.apply_along_axis(_os, ax, x)


def core_cfar_os_2d(
    data: Any,
    guard: int | tuple[int, int] | list[int] | np.ndarray,
    trailing: int | tuple[int, int] | list[int] | np.ndarray,
    k: int,
    pfa: float = 1e-5,
    detector: str = "squarelaw",
    offset: float | None = None,
) -> np.ndarray:
    x = np.asarray(data)
    if x.ndim != 2:
        raise ValueError("cfar_os_2d expects 2-D data")
    if np.iscomplexobj(x):
        raise ValueError("Input data should not be complex.")

    g0, g1 = _as_pair(guard)
    t0, t1 = _as_pair(trailing)
    k_i = int(k)
    tg0 = t0 + g0
    tg1 = t1 + g1
    t_num = (2 * tg0 + 1) * (2 * tg1 + 1)
    g_num = (2 * g0 + 1) * (2 * g1 + 1)
    n_train = t_num - g_num
    if n_train <= 0:
        raise ValueError("No trailing bins!")
    if k_i < 0 or k_i >= n_train:
        raise ValueError("k out of range for ordered statistics training bins")

    if offset is None:
        if detector == "squarelaw":
            a = float(_os_cfar_threshold(k_i, n_train, float(pfa)))
        elif detector == "linear":
            a = float(np.sqrt(_os_cfar_threshold(k_i, n_train, float(pfa))))
        else:
            raise ValueError("`detector` can only be `linear` or `squarelaw`.")
    else:
        a = float(offset)

    if (k_i < (n_train / 2.0)) or (k_i > n_train):
        warn(f"k is usually in (N/2, N), N={n_train}; typical k~0.75N", RuntimeWarning)

    cfar_mask = np.ones((2 * tg0 + 1, 2 * tg1 + 1), dtype=bool)
    cfar_mask[t0 : (t0 + 2 * g0 + 1), t1 : (t1 + 2 * g1 + 1)] = False

    h, w = x.shape
    out = np.zeros_like(x, dtype=np.float64)
    for i in range(h):
        wi = np.mod(np.arange(i - tg0, i + tg0 + 1, 1), h).astype(np.int64)
        for j in range(w):
            wj = np.mod(np.arange(j - tg1, j + tg1 + 1, 1), w).astype(np.int64)
            gx, gy = np.meshgrid(wi, wj, indexing="ij")
            sample_cube = x[gx, gy]
            samples = np.sort(sample_cube[cfar_mask].reshape(-1))
            out[i, j] = a * samples[k_i]
    return out


def core_doa_music(
    covmat: Any,
    nsig: int,
    spacing: float = 0.5,
    scanangles: Any = range(-90, 91),
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    cov = np.asarray(covmat, dtype=np.complex128)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ValueError("covmat must be square 2-D matrix")
    n_array = cov.shape[0]
    nsig_i = int(nsig)
    if nsig_i <= 0 or nsig_i >= n_array:
        raise ValueError("nsig must be in [1, n_array-1]")
    scan, sv = _steering_vector(n_array, float(spacing), scanangles)

    _, eigvecs = np.linalg.eigh(cov)
    noise_subspace = eigvecs[:, :-nsig_i]
    denom = np.linalg.norm(noise_subspace.T.conj() @ sv, axis=0)
    denom = np.maximum(denom, np.finfo(np.float64).tiny)
    pseudo = 1.0 / denom
    pseudo = np.maximum(pseudo, np.finfo(np.float64).tiny)
    ps_db = 10.0 * np.log10(pseudo / np.min(pseudo))
    peaks, _ = find_peaks(ps_db)
    if peaks.size == 0:
        doa_idx = np.argsort(ps_db)[-nsig_i:]
    else:
        doa_idx = peaks[np.argsort(ps_db[peaks])[-nsig_i:]]
    doa_idx = np.asarray(doa_idx, dtype=np.int64)
    return scan[doa_idx], doa_idx, ps_db


def core_doa_root_music(covmat: Any, nsig: int, spacing: float = 0.5) -> np.ndarray:
    cov = np.asarray(covmat, dtype=np.complex128)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ValueError("covmat must be square 2-D matrix")
    n_cov = cov.shape[0]
    nsig_i = int(nsig)
    if nsig_i <= 0 or nsig_i >= n_cov:
        raise ValueError("nsig must be in [1, n_array-1]")

    _, eigvecs = np.linalg.eigh(cov)
    noise_subspace = eigvecs[:, :-nsig_i]
    noise_mat = noise_subspace @ noise_subspace.T.conj()

    coeff = np.zeros((n_cov - 1,), dtype=np.complex128)
    for i in range(1, n_cov):
        coeff[i - 1] = np.trace(noise_mat, i)
    coeff = np.hstack((coeff[::-1], np.trace(noise_mat), np.conj(coeff)))
    roots = np.roots(coeff)

    mask = np.abs(roots) <= 1.0
    on_uc = np.where(np.isclose(np.abs(roots), 1.0))[0]
    for i in on_uc:
        near = np.argsort(np.abs(roots - roots[i]))
        if near.size > 1:
            mask[near[1]] = False

    roots = roots[mask]
    if roots.size < nsig_i:
        roots = np.roots(coeff)
        order = np.argsort(np.abs(np.abs(roots) - 1.0))
        roots = roots[order[:nsig_i]]
    else:
        order = np.argsort(1.0 - np.abs(roots))
        roots = roots[order[:nsig_i]]

    sin_vals = np.angle(roots) / (2.0 * np.pi * float(spacing))
    sin_vals = np.clip(sin_vals, -1.0, 1.0)
    return np.degrees(np.arcsin(sin_vals))


def core_doa_esprit(covmat: Any, nsig: int, spacing: float = 0.5) -> np.ndarray:
    cov = np.asarray(covmat, dtype=np.complex128)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ValueError("covmat must be square 2-D matrix")
    n_array = cov.shape[0]
    nsig_i = int(nsig)
    if nsig_i <= 0 or nsig_i >= n_array:
        raise ValueError("nsig must be in [1, n_array-1]")

    _, eigvecs = np.linalg.eigh(cov)
    signal_subspace = eigvecs[:, -nsig_i:]
    phi = linalg.pinv(signal_subspace[:-1]) @ signal_subspace[1:]
    eigs = np.linalg.eigvals(phi)
    sin_vals = np.angle(eigs) / np.pi / (float(spacing) / 0.5)
    sin_vals = np.clip(sin_vals, -1.0, 1.0)
    return np.degrees(np.arcsin(sin_vals))


def core_doa_iaa(
    beam_vect: Any,
    steering_vect: Any,
    num_it: int = 15,
    p_init: Any | None = None,
) -> np.ndarray:
    beam = np.asarray(beam_vect, dtype=np.complex128)
    steering = np.asarray(steering_vect, dtype=np.complex128)
    if beam.ndim != 2 or steering.ndim != 2:
        raise ValueError("beam_vect and steering_vect must be 2-D")
    if beam.shape[0] != steering.shape[0]:
        raise ValueError("beam_vect and steering_vect first dimension must match")

    num_grid = steering.shape[1]
    nit = max(1, int(num_it))
    tiny = np.finfo(np.float64).tiny

    if p_init is None:
        spectrum = np.zeros(num_grid, dtype=np.complex128)
        for i in range(num_grid):
            a = np.conj(steering[:, i][np.newaxis, :])
            denom = (a @ a.conj().T) ** 2
            denom = np.where(np.abs(denom) < tiny, tiny, denom)
            spectrum[i] = (np.mean(np.abs(a @ beam) ** 2) / denom).item()
    else:
        spectrum = np.asarray(p_init, dtype=np.complex128).reshape(-1)
        if spectrum.shape[0] != num_grid:
            raise ValueError("p_init length must match steering_vect.shape[1]")

    for _ in range(nit - 1):
        p_diag = np.diag(spectrum.flatten())
        r = steering @ p_diag @ steering.conj().T
        r_inv = np.linalg.inv(r)
        for i in range(num_grid):
            a = np.conj(steering[:, i][np.newaxis, :])
            denom = (a @ r_inv @ a.conj().T)
            denom = np.where(np.abs(denom) < tiny, tiny, denom)
            spec = a @ r_inv @ beam / denom
            spectrum[i] = np.mean(np.abs(spec) ** 2)

    return 10.0 * np.log10(np.maximum(np.real(spectrum), tiny))


def core_doa_bartlett(
    covmat: Any,
    spacing: float = 0.5,
    scanangles: Any = range(-90, 91),
) -> np.ndarray:
    cov = np.asarray(covmat, dtype=np.complex128)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ValueError("covmat must be square 2-D matrix")
    n_array = cov.shape[0]
    _, sv = _steering_vector(n_array, float(spacing), scanangles)
    ps = np.sum(np.conj(sv) * (cov @ sv), axis=0).real
    return 10.0 * np.log10(np.maximum(ps, np.finfo(np.float64).tiny))


def core_doa_capon(
    covmat: Any,
    spacing: float = 0.5,
    scanangles: Any = range(-90, 91),
) -> np.ndarray:
    cov = np.asarray(covmat, dtype=np.complex128)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ValueError("covmat must be square 2-D matrix")
    n_array = cov.shape[0]
    scan, sv = _steering_vector(n_array, float(spacing), scanangles)

    inv_cov = linalg.pinv(cov + np.eye(n_array, dtype=np.complex128) * 1e-9)
    ps = np.zeros(scan.shape, dtype=np.float64)
    for i in range(scan.shape[0]):
        s = sv[:, i]
        den = s.T.conj() @ inv_cov @ s
        if np.abs(den) < np.finfo(np.float64).tiny:
            den = np.finfo(np.float64).tiny
        w = inv_cov @ s / den
        ps[i] = np.abs(w.T.conj() @ cov @ w)
    return 10.0 * np.log10(np.maximum(ps, np.finfo(np.float64).tiny))


__all__ = [
    "core_range_fft",
    "core_doppler_fft",
    "core_range_doppler_fft",
    "core_cfar_ca_1d",
    "core_cfar_ca_2d",
    "core_cfar_os_1d",
    "core_cfar_os_2d",
    "core_doa_music",
    "core_doa_root_music",
    "core_doa_esprit",
    "core_doa_iaa",
    "core_doa_bartlett",
    "core_doa_capon",
]
