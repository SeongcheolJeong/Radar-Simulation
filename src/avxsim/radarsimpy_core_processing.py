from __future__ import annotations

from typing import Any

import numpy as np


def _normalize_axis(axis: int, ndim: int) -> int:
    if ndim <= 0:
        raise ValueError("array must have at least one dimension")
    a = int(axis)
    if a < 0:
        a += ndim
    if a < 0 or a >= ndim:
        raise ValueError(f"axis out of range: axis={axis}, ndim={ndim}")
    return a


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
    axis: int = -1,
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
