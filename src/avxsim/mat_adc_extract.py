from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

import numpy as np


def load_adc_from_mat(path: str, variable: Optional[str] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(str(p))

    try:
        return _load_with_scipy(p, variable=variable)
    except Exception as exc_scipy:
        try:
            return _load_with_h5py(p, variable=variable)
        except Exception as exc_h5:
            raise RuntimeError(
                "failed to load MAT file; install scipy (MAT v5) or h5py (MAT v7.3). "
                f"scipy error: {exc_scipy}; h5py error: {exc_h5}"
            )


def select_4d_numeric_array(mapping: Mapping[str, Any], variable: Optional[str] = None) -> Tuple[np.ndarray, str]:
    if variable is not None:
        key = str(variable)
        if key not in mapping:
            raise ValueError(f"variable not found: {key}")
        arr = np.asarray(mapping[key])
        if arr.ndim != 4:
            raise ValueError(f"variable '{key}' is not 4D")
        if not np.issubdtype(arr.dtype, np.number):
            raise ValueError(f"variable '{key}' must be numeric")
        return arr, key

    best_key = None
    best_arr = None
    best_size = -1
    for key, value in mapping.items():
        if str(key).startswith("__"):
            continue
        arr = np.asarray(value)
        if arr.ndim != 4:
            continue
        if not np.issubdtype(arr.dtype, np.number):
            continue
        size = int(arr.size)
        if size > best_size:
            best_size = size
            best_arr = arr
            best_key = str(key)

    if best_arr is None or best_key is None:
        raise ValueError("no 4D numeric array found in MAT content")
    return best_arr, best_key


def _load_with_scipy(path: Path, variable: Optional[str]) -> Tuple[np.ndarray, Dict[str, Any]]:
    try:
        from scipy.io import loadmat  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"scipy import failed: {exc}")

    payload = loadmat(str(path))
    arr, key = select_4d_numeric_array(payload, variable=variable)
    return np.asarray(arr), {
        "source": str(path),
        "loader": "scipy.io.loadmat",
        "variable": str(key),
        "shape": [int(x) for x in np.asarray(arr).shape],
        "dtype": str(np.asarray(arr).dtype),
    }


def _load_with_h5py(path: Path, variable: Optional[str]) -> Tuple[np.ndarray, Dict[str, Any]]:
    try:
        import h5py  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"h5py import failed: {exc}")

    with h5py.File(str(path), "r") as f:
        if variable is not None:
            if variable not in f:
                raise ValueError(f"variable not found in HDF5 MAT: {variable}")
            ds = f[variable]
            arr = np.asarray(ds)
            if arr.ndim != 4:
                raise ValueError(f"variable '{variable}' is not 4D")
            if not np.issubdtype(arr.dtype, np.number):
                raise ValueError(f"variable '{variable}' must be numeric")
            key = str(variable)
        else:
            key, arr = _pick_h5_4d_dataset(f)

    return np.asarray(arr), {
        "source": str(path),
        "loader": "h5py",
        "variable": str(key),
        "shape": [int(x) for x in np.asarray(arr).shape],
        "dtype": str(np.asarray(arr).dtype),
    }


def _pick_h5_4d_dataset(group) -> Tuple[str, np.ndarray]:
    candidates: List[Tuple[str, Any]] = []

    def _walk(prefix: str, node):
        import h5py  # type: ignore

        if isinstance(node, h5py.Dataset):
            arr = np.asarray(node)
            if arr.ndim == 4 and np.issubdtype(arr.dtype, np.number):
                candidates.append((prefix, arr))
            return
        for k in node.keys():
            _walk(f"{prefix}/{k}" if prefix else str(k), node[k])

    _walk("", group)
    if len(candidates) == 0:
        raise ValueError("no 4D numeric dataset found in HDF5 MAT")

    candidates_sorted = sorted(candidates, key=lambda kv: int(np.asarray(kv[1]).size), reverse=True)
    return str(candidates_sorted[0][0]), np.asarray(candidates_sorted[0][1])
