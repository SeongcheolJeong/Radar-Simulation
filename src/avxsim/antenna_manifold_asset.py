from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class ComplexManifoldAsset:
    freq_hz: np.ndarray
    theta_deg: np.ndarray
    phi_deg: np.ndarray
    tx_etheta: np.ndarray
    tx_ephi: np.ndarray
    rx_etheta: np.ndarray
    rx_ephi: np.ndarray
    source_path: str

    def tx_jones_from_azel(
        self,
        frequency_hz: float,
        az_deg: float,
        el_deg: float,
    ) -> np.ndarray:
        theta_query = 90.0 - float(el_deg)
        etheta = _interp3_periodic_phi(
            freq_grid=self.freq_hz,
            theta_grid=self.theta_deg,
            phi_grid=self.phi_deg,
            field=self.tx_etheta,
            freq_query=float(frequency_hz),
            theta_query=theta_query,
            phi_query=float(az_deg),
        )
        ephi = _interp3_periodic_phi(
            freq_grid=self.freq_hz,
            theta_grid=self.theta_deg,
            phi_grid=self.phi_deg,
            field=self.tx_ephi,
            freq_query=float(frequency_hz),
            theta_query=theta_query,
            phi_query=float(az_deg),
        )
        return np.asarray([etheta, ephi], dtype=np.complex128)

    def rx_jones_from_azel(
        self,
        frequency_hz: float,
        az_deg: float,
        el_deg: float,
    ) -> np.ndarray:
        theta_query = 90.0 - float(el_deg)
        etheta = _interp3_periodic_phi(
            freq_grid=self.freq_hz,
            theta_grid=self.theta_deg,
            phi_grid=self.phi_deg,
            field=self.rx_etheta,
            freq_query=float(frequency_hz),
            theta_query=theta_query,
            phi_query=float(az_deg),
        )
        ephi = _interp3_periodic_phi(
            freq_grid=self.freq_hz,
            theta_grid=self.theta_deg,
            phi_grid=self.phi_deg,
            field=self.rx_ephi,
            freq_query=float(frequency_hz),
            theta_query=theta_query,
            phi_query=float(az_deg),
        )
        return np.asarray([etheta, ephi], dtype=np.complex128)

    def monostatic_gain_from_azel(
        self,
        frequency_hz: float,
        az_deg: float,
        el_deg: float,
        tx_pol_weights: Sequence[complex] = (1.0 + 0.0j, 0.0 + 0.0j),
        rx_pol_weights: Sequence[complex] = (1.0 + 0.0j, 0.0 + 0.0j),
    ) -> complex:
        tx_jones = self.tx_jones_from_azel(
            frequency_hz=float(frequency_hz),
            az_deg=float(az_deg),
            el_deg=float(el_deg),
        )
        rx_jones = self.rx_jones_from_azel(
            frequency_hz=float(frequency_hz),
            az_deg=float(az_deg),
            el_deg=float(el_deg),
        )
        w_tx = _resolve_pol_weights(tx_pol_weights, "tx_pol_weights")
        w_rx = _resolve_pol_weights(rx_pol_weights, "rx_pol_weights")
        tx_gain = complex(w_tx[0]) * tx_jones[0] + complex(w_tx[1]) * tx_jones[1]
        rx_gain = complex(w_rx[0]) * rx_jones[0] + complex(w_rx[1]) * rx_jones[1]
        return complex(tx_gain * rx_gain)


def load_complex_manifold_asset(path: str) -> ComplexManifoldAsset:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"complex manifold asset not found: {p}")

    suffix = p.suffix.lower()
    if suffix == ".npz":
        raw = _load_npz_arrays(p)
    elif suffix in {".h5", ".hdf5"}:
        raw = _load_hdf5_arrays(p)
    else:
        raise ValueError(f"unsupported manifold asset format: {p.suffix} (expected .npz/.h5/.hdf5)")

    return _build_asset_from_arrays(raw=raw, source_path=str(p))


def _load_npz_arrays(path: Path) -> Dict[str, np.ndarray]:
    out: Dict[str, np.ndarray] = {}
    with np.load(str(path), allow_pickle=False) as payload:
        for key in payload.files:
            out[str(key)] = np.asarray(payload[key])
    if not out:
        raise ValueError(f"complex manifold npz is empty: {path}")
    return out


def _load_hdf5_arrays(path: Path) -> Dict[str, np.ndarray]:
    try:
        import h5py  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise ValueError("loading .h5/.hdf5 manifold assets requires h5py") from exc

    out: Dict[str, np.ndarray] = {}
    with h5py.File(str(path), "r") as h5:
        _collect_hdf5_arrays(out, h5)
    if not out:
        raise ValueError(f"complex manifold hdf5 has no datasets: {path}")
    return out


def _collect_hdf5_arrays(out: Dict[str, np.ndarray], group: Any, prefix: str = "") -> None:
    for key, value in group.items():
        name = str(key) if prefix == "" else f"{prefix}/{key}"
        if hasattr(value, "shape") and hasattr(value, "dtype"):
            out[name] = np.asarray(value)
            continue
        if hasattr(value, "items"):
            _collect_hdf5_arrays(out, value, prefix=name)


def _build_asset_from_arrays(
    raw: Mapping[str, np.ndarray],
    source_path: str,
) -> ComplexManifoldAsset:
    key_index = _build_key_index(raw)

    freq_hz = _resolve_axis(
        key_index=key_index,
        aliases=("freq_hz", "frequency_hz", "freq", "f_hz"),
        key_name="freq_hz",
    )
    theta_deg = _resolve_axis(
        key_index=key_index,
        aliases=("theta_deg", "theta", "theta_grid_deg"),
        key_name="theta_deg",
    )
    phi_deg = _resolve_axis(
        key_index=key_index,
        aliases=("phi_deg", "phi", "phi_grid_deg"),
        key_name="phi_deg",
    )

    n_freq = int(freq_hz.size)
    n_theta = int(theta_deg.size)
    n_phi = int(phi_deg.size)

    tx_etheta = _resolve_complex_grid(
        key_index=key_index,
        stem_aliases=("tx_etheta", "etheta_tx", "txetheta"),
        key_name="tx_etheta",
        n_freq=n_freq,
        n_theta=n_theta,
        n_phi=n_phi,
    )
    tx_ephi = _resolve_complex_grid(
        key_index=key_index,
        stem_aliases=("tx_ephi", "ephi_tx", "txephi"),
        key_name="tx_ephi",
        n_freq=n_freq,
        n_theta=n_theta,
        n_phi=n_phi,
    )
    rx_etheta = _resolve_complex_grid(
        key_index=key_index,
        stem_aliases=("rx_etheta", "etheta_rx", "rxetheta"),
        key_name="rx_etheta",
        n_freq=n_freq,
        n_theta=n_theta,
        n_phi=n_phi,
    )
    rx_ephi = _resolve_complex_grid(
        key_index=key_index,
        stem_aliases=("rx_ephi", "ephi_rx", "rxephi"),
        key_name="rx_ephi",
        n_freq=n_freq,
        n_theta=n_theta,
        n_phi=n_phi,
    )

    freq_order = np.argsort(freq_hz)
    theta_order = np.argsort(theta_deg)
    phi_order = np.argsort(phi_deg)

    freq_hz = freq_hz[freq_order]
    theta_deg = theta_deg[theta_order]
    phi_deg = phi_deg[phi_order]

    tx_etheta = tx_etheta[np.ix_(freq_order, theta_order, phi_order)]
    tx_ephi = tx_ephi[np.ix_(freq_order, theta_order, phi_order)]
    rx_etheta = rx_etheta[np.ix_(freq_order, theta_order, phi_order)]
    rx_ephi = rx_ephi[np.ix_(freq_order, theta_order, phi_order)]

    _validate_strictly_increasing(freq_hz, "freq_hz")
    _validate_strictly_increasing(theta_deg, "theta_deg")
    _validate_strictly_increasing(phi_deg, "phi_deg")

    return ComplexManifoldAsset(
        freq_hz=freq_hz,
        theta_deg=theta_deg,
        phi_deg=phi_deg,
        tx_etheta=tx_etheta,
        tx_ephi=tx_ephi,
        rx_etheta=rx_etheta,
        rx_ephi=rx_ephi,
        source_path=str(source_path),
    )


def _build_key_index(raw: Mapping[str, np.ndarray]) -> Dict[str, np.ndarray]:
    out: Dict[str, np.ndarray] = {}
    for key, value in raw.items():
        arr = np.asarray(value)
        variants = {
            str(key),
            str(key).split("/")[-1],
        }
        for variant in variants:
            out[_normalize_key(variant)] = arr
    return out


def _normalize_key(value: str) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def _resolve_axis(
    key_index: Mapping[str, np.ndarray],
    aliases: Sequence[str],
    key_name: str,
) -> np.ndarray:
    arr = _resolve_array_by_alias(key_index=key_index, aliases=aliases, key_name=key_name)
    out = np.asarray(arr, dtype=np.float64).reshape(-1)
    if out.size <= 0:
        raise ValueError(f"{key_name} must be non-empty")
    if not np.all(np.isfinite(out)):
        raise ValueError(f"{key_name} must contain finite values")
    return out


def _resolve_complex_grid(
    key_index: Mapping[str, np.ndarray],
    stem_aliases: Sequence[str],
    key_name: str,
    n_freq: int,
    n_theta: int,
    n_phi: int,
) -> np.ndarray:
    for stem in stem_aliases:
        direct = key_index.get(_normalize_key(stem))
        if direct is not None:
            arr = np.asarray(direct)
            if np.iscomplexobj(arr):
                return _coerce_field_shape(
                    arr=arr,
                    key_name=key_name,
                    n_freq=n_freq,
                    n_theta=n_theta,
                    n_phi=n_phi,
                )

    re_arr = None
    im_arr = None
    for stem in stem_aliases:
        stem_norm = _normalize_key(stem)
        if re_arr is None:
            re_arr = key_index.get(stem_norm + "re")
        if re_arr is None:
            re_arr = key_index.get(stem_norm + "real")
        if im_arr is None:
            im_arr = key_index.get(stem_norm + "im")
        if im_arr is None:
            im_arr = key_index.get(stem_norm + "imag")
    if re_arr is None or im_arr is None:
        raise ValueError(f"missing complex field arrays for {key_name}")

    combined = np.asarray(re_arr, dtype=np.float64) + 1j * np.asarray(im_arr, dtype=np.float64)
    return _coerce_field_shape(
        arr=combined,
        key_name=key_name,
        n_freq=n_freq,
        n_theta=n_theta,
        n_phi=n_phi,
    )


def _coerce_field_shape(
    arr: np.ndarray,
    key_name: str,
    n_freq: int,
    n_theta: int,
    n_phi: int,
) -> np.ndarray:
    v = np.asarray(arr, dtype=np.complex128)
    if v.ndim == 2 and n_freq == 1 and v.shape == (n_theta, n_phi):
        v = v.reshape(1, n_theta, n_phi)
    elif v.ndim == 3 and v.shape == (n_theta, n_phi, n_freq):
        v = np.transpose(v, (2, 0, 1))
    elif v.ndim == 3 and v.shape == (n_theta, n_freq, n_phi):
        v = np.transpose(v, (1, 0, 2))
    elif v.ndim == 3 and v.shape == (n_phi, n_theta, n_freq):
        v = np.transpose(v, (2, 1, 0))
    elif v.ndim == 3 and v.shape == (n_freq, n_phi, n_theta):
        v = np.transpose(v, (0, 2, 1))
    if v.shape != (n_freq, n_theta, n_phi):
        raise ValueError(
            f"{key_name} shape mismatch: got {tuple(v.shape)}, expected {(n_freq, n_theta, n_phi)}"
        )
    if not np.all(np.isfinite(np.real(v))) or not np.all(np.isfinite(np.imag(v))):
        raise ValueError(f"{key_name} must contain finite values")
    return v


def _resolve_array_by_alias(
    key_index: Mapping[str, np.ndarray],
    aliases: Sequence[str],
    key_name: str,
) -> np.ndarray:
    for alias in aliases:
        key = _normalize_key(alias)
        if key in key_index:
            return np.asarray(key_index[key])
    raise ValueError(f"missing required manifold axis: {key_name}")


def _resolve_pol_weights(value: Sequence[complex], key_name: str) -> Tuple[complex, complex]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{key_name} must be length-2 sequence")
    arr = np.asarray(list(value), dtype=np.complex128).reshape(-1)
    if arr.size != 2:
        raise ValueError(f"{key_name} must be length 2")
    return complex(arr[0]), complex(arr[1])


def _validate_strictly_increasing(values: np.ndarray, key_name: str) -> None:
    if values.size <= 0:
        raise ValueError(f"{key_name} must be non-empty")
    diffs = np.diff(values)
    if np.any(diffs <= 0.0):
        raise ValueError(f"{key_name} must be strictly increasing and unique")


def _interp3_periodic_phi(
    freq_grid: np.ndarray,
    theta_grid: np.ndarray,
    phi_grid: np.ndarray,
    field: np.ndarray,
    freq_query: float,
    theta_query: float,
    phi_query: float,
) -> complex:
    if freq_grid.ndim != 1 or theta_grid.ndim != 1 or phi_grid.ndim != 1:
        raise ValueError("freq/theta/phi grids must be 1D")
    if field.shape != (freq_grid.size, theta_grid.size, phi_grid.size):
        raise ValueError("field shape mismatch")

    fq = float(np.clip(freq_query, float(freq_grid[0]), float(freq_grid[-1])))
    i0, i1, wf = _find_interval(freq_grid, fq)
    f0 = _interp2_periodic_phi(
        theta_grid=theta_grid,
        phi_grid=phi_grid,
        field=field[i0, :, :],
        theta_query=theta_query,
        phi_query=phi_query,
    )
    f1 = _interp2_periodic_phi(
        theta_grid=theta_grid,
        phi_grid=phi_grid,
        field=field[i1, :, :],
        theta_query=theta_query,
        phi_query=phi_query,
    )
    return complex((1.0 - wf) * f0 + wf * f1)


def _interp2_periodic_phi(
    theta_grid: np.ndarray,
    phi_grid: np.ndarray,
    field: np.ndarray,
    theta_query: float,
    phi_query: float,
) -> complex:
    if theta_grid.ndim != 1 or phi_grid.ndim != 1:
        raise ValueError("theta_grid and phi_grid must be 1D")
    if field.shape != (theta_grid.size, phi_grid.size):
        raise ValueError("field shape mismatch with theta/phi grids")

    tq = float(np.clip(theta_query, float(theta_grid[0]), float(theta_grid[-1])))

    p0 = float(phi_grid[0])
    pq = ((float(phi_query) - p0) % 360.0) + p0
    phi_ext = np.concatenate([phi_grid, [phi_grid[0] + 360.0]])
    field_ext = np.concatenate([field, field[:, :1]], axis=1)

    i0, i1, wt = _find_interval(theta_grid, tq)
    j0, j1, wp = _find_interval(phi_ext, pq)

    f00 = field_ext[i0, j0]
    f01 = field_ext[i0, j1]
    f10 = field_ext[i1, j0]
    f11 = field_ext[i1, j1]
    top = (1.0 - wp) * f00 + wp * f01
    bot = (1.0 - wp) * f10 + wp * f11
    return complex((1.0 - wt) * top + wt * bot)


def _find_interval(grid: np.ndarray, x: float) -> Tuple[int, int, float]:
    if grid.size == 1:
        return 0, 0, 0.0
    if x <= grid[0]:
        return 0, 1, 0.0
    if x >= grid[-1]:
        return grid.size - 2, grid.size - 1, 1.0
    hi = int(np.searchsorted(grid, x, side="right"))
    lo = hi - 1
    x0 = float(grid[lo])
    x1 = float(grid[hi])
    if x1 == x0:
        return lo, hi, 0.0
    return lo, hi, float((x - x0) / (x1 - x0))
