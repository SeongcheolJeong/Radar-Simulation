import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import numpy as np


def fit_global_jones_matrix(
    tx_jones: np.ndarray,
    rx_jones: np.ndarray,
    observed_gain: np.ndarray,
    path_matrices: Optional[np.ndarray] = None,
    ridge: float = 0.0,
) -> Dict[str, Any]:
    """
    Fit global Jones matrix J (2x2) from samples:
      observed_gain[n] ~= rx_jones[n]^H * J * path_matrices[n] * tx_jones[n]

    If path_matrices is None, identity is used for each sample.
    """
    tx = np.asarray(tx_jones, dtype=np.complex128)
    rx = np.asarray(rx_jones, dtype=np.complex128)
    y = np.asarray(observed_gain, dtype=np.complex128).reshape(-1)

    if tx.ndim != 2 or tx.shape[1] != 2:
        raise ValueError("tx_jones must have shape (N, 2)")
    if rx.ndim != 2 or rx.shape[1] != 2:
        raise ValueError("rx_jones must have shape (N, 2)")
    if tx.shape[0] != rx.shape[0] or tx.shape[0] != y.size:
        raise ValueError("tx_jones, rx_jones, observed_gain must have matching sample count")

    n = int(y.size)
    if n <= 0:
        raise ValueError("at least one calibration sample is required")
    pmat = _resolve_path_matrices(path_matrices, n)
    a = np.zeros((n, 4), dtype=np.complex128)
    for i in range(n):
        q = pmat[i] @ tx[i]
        a[i, :] = np.asarray(
            [
                np.conj(rx[i, 0]) * q[0],
                np.conj(rx[i, 0]) * q[1],
                np.conj(rx[i, 1]) * q[0],
                np.conj(rx[i, 1]) * q[1],
            ],
            dtype=np.complex128,
        )

    j_vec = _solve_least_squares(a, y, ridge=float(ridge))
    j = j_vec.reshape(2, 2)

    j_eff = np.einsum("ij,njk->nik", j, pmat)
    y_hat = np.einsum("ni,nij,nj->n", np.conj(rx), j_eff, tx)
    resid = y - y_hat
    rmse = float(np.sqrt(np.mean(np.abs(resid) ** 2)))
    rel_rmse = rmse / float(np.sqrt(np.mean(np.abs(y) ** 2)) + 1e-12)
    nmse = float(np.mean(np.abs(resid) ** 2) / (np.mean(np.abs(y) ** 2) + 1e-12))
    corr = _complex_correlation(y, y_hat)

    return {
        "global_jones_matrix": j,
        "predicted_gain": y_hat,
        "residual_gain": resid,
        "metrics": {
            "rmse": rmse,
            "relative_rmse": float(rel_rmse),
            "nmse": nmse,
            "complex_correlation_mag": float(np.abs(corr)),
            "complex_correlation_phase_rad": float(np.angle(corr)),
            "sample_count": n,
            "ridge": float(ridge),
        },
    }


def apply_global_jones_matrix(
    tx_jones: np.ndarray,
    rx_jones: np.ndarray,
    global_jones_matrix: np.ndarray,
    path_matrices: Optional[np.ndarray] = None,
) -> np.ndarray:
    tx = np.asarray(tx_jones, dtype=np.complex128)
    rx = np.asarray(rx_jones, dtype=np.complex128)
    j = _resolve_jones_matrix(global_jones_matrix)
    if tx.ndim != 2 or tx.shape[1] != 2:
        raise ValueError("tx_jones must have shape (N, 2)")
    if rx.ndim != 2 or rx.shape[1] != 2:
        raise ValueError("rx_jones must have shape (N, 2)")
    if tx.shape[0] != rx.shape[0]:
        raise ValueError("tx_jones and rx_jones must have matching sample count")
    pmat = _resolve_path_matrices(path_matrices, int(tx.shape[0]))
    return np.einsum("ni,ij,njk,nk->n", np.conj(rx), j, pmat, tx)


def load_global_jones_matrix_json(path: str) -> np.ndarray:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, Mapping) and "global_jones_matrix" in payload:
        payload = payload["global_jones_matrix"]
    return parse_jones_matrix(payload)


def save_global_jones_matrix_json(
    out_path: str,
    matrix: np.ndarray,
    metrics: Optional[Mapping[str, Any]] = None,
) -> None:
    j = _resolve_jones_matrix(matrix)
    payload: Dict[str, Any] = {
        "global_jones_matrix": [
            {"re": float(np.real(j[0, 0])), "im": float(np.imag(j[0, 0]))},
            {"re": float(np.real(j[0, 1])), "im": float(np.imag(j[0, 1]))},
            {"re": float(np.real(j[1, 0])), "im": float(np.imag(j[1, 0]))},
            {"re": float(np.real(j[1, 1])), "im": float(np.imag(j[1, 1]))},
        ]
    }
    if metrics is not None:
        payload["metrics"] = _to_jsonable(metrics)
    Path(out_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_jones_matrix(value: Any) -> np.ndarray:
    if isinstance(value, Mapping):
        keys = ("m00", "m01", "m10", "m11")
        if all(k in value for k in keys):
            vals = [value[k] for k in keys]
            return np.asarray([_parse_complex(v) for v in vals], dtype=np.complex128).reshape(2, 2)
        raise ValueError("dict Jones matrix must contain m00,m01,m10,m11")

    arr = np.asarray(value)
    if arr.ndim == 2 and arr.shape == (2, 2):
        flat = [_parse_complex(v) for v in arr.reshape(-1).tolist()]
        return np.asarray(flat, dtype=np.complex128).reshape(2, 2)
    if arr.ndim == 1 and arr.size == 4:
        return np.asarray([_parse_complex(v) for v in arr.tolist()], dtype=np.complex128).reshape(2, 2)
    if isinstance(value, (list, tuple)):
        flat = []
        for v in value:
            if isinstance(v, (list, tuple)) and len(v) == 2 and not np.iscomplexobj(v):
                flat.append(complex(float(v[0]), float(v[1])))
            else:
                flat.append(_parse_complex(v))
        if len(flat) == 4:
            return np.asarray(flat, dtype=np.complex128).reshape(2, 2)
    raise ValueError("Jones matrix must be shape (2,2), length-4, or dict m00/m01/m10/m11")


def _resolve_jones_matrix(mat: Any) -> np.ndarray:
    return parse_jones_matrix(mat)


def _resolve_path_matrices(path_matrices: Optional[np.ndarray], n: int) -> np.ndarray:
    if path_matrices is None:
        out = np.zeros((n, 2, 2), dtype=np.complex128)
        out[:, 0, 0] = 1.0 + 0.0j
        out[:, 1, 1] = 1.0 + 0.0j
        return out
    p = np.asarray(path_matrices, dtype=np.complex128)
    if p.ndim != 3 or p.shape[1:] != (2, 2):
        raise ValueError("path_matrices must have shape (N,2,2)")
    if p.shape[0] != n:
        raise ValueError("path_matrices sample count mismatch")
    return p


def _solve_least_squares(a: np.ndarray, y: np.ndarray, ridge: float) -> np.ndarray:
    if ridge < 0:
        raise ValueError("ridge must be non-negative")
    if ridge == 0:
        x, *_ = np.linalg.lstsq(a, y, rcond=None)
        return x
    # Avoid platform-specific complex matmul runtime warnings on some BLAS builds.
    gram = np.einsum("ni,nj->ij", np.conj(a), a)
    rhs = np.einsum("ni,n->i", np.conj(a), y)
    reg = ridge * np.eye(gram.shape[0], dtype=np.complex128)
    return np.linalg.solve(gram + reg, rhs)


def _complex_correlation(x: np.ndarray, y: np.ndarray) -> complex:
    x = np.asarray(x, dtype=np.complex128).reshape(-1)
    y = np.asarray(y, dtype=np.complex128).reshape(-1)
    den = np.sqrt(np.sum(np.abs(x) ** 2) * np.sum(np.abs(y) ** 2)) + 1e-12
    return complex(np.vdot(x, y) / den)


def _parse_complex(value: Any) -> complex:
    if isinstance(value, Mapping):
        return complex(float(value.get("re", 0.0)), float(value.get("im", 0.0)))
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return complex(float(value[0]), float(value[1]))
    return complex(value)


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, (np.complexfloating, complex)):
        return {"re": float(np.real(value)), "im": float(np.imag(value))}
    return value
