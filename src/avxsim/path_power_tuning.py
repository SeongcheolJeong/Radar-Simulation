import csv
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np

from .constants import C0
from .hybrid_pcode import (
    calculate_reflecting_path_power,
    calculate_scattering_path_power,
)


DEFAULT_PATH_POWER_COLUMN_MAP: Dict[str, str] = {
    "range_m": "range_m",
    "az_rad": "az_rad",
    "el_rad": "el_rad",
    "observed_amp": "observed_amp",
    "scenario_id": "scenario_id",
}


DEFAULT_REFLECTION_GRID: Dict[str, Sequence[float]] = {
    "range_power_exponent": [2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
}


DEFAULT_SCATTERING_GRID: Dict[str, Sequence[float]] = {
    "range_power_exponent": [2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
    "elevation_power": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
    "azimuth_mix": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
    "azimuth_power": [1.0, 2.0, 3.0, 4.0],
}


def build_path_power_samples_from_csv(
    csv_path: str,
    column_map: Optional[Mapping[str, str]] = None,
    delimiter: str = ",",
) -> Dict[str, Any]:
    cmap = dict(DEFAULT_PATH_POWER_COLUMN_MAP)
    if column_map is not None:
        for key, value in column_map.items():
            cmap[str(key)] = str(value)

    rows = []
    with Path(csv_path).open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("CSV must contain a header row")
        _validate_required(reader.fieldnames, ["range_m", "observed_amp"], cmap)

        for row_idx, row in enumerate(reader, start=2):
            range_m = _get_float(row, cmap["range_m"], row_idx)
            observed_amp = _get_float(row, cmap["observed_amp"], row_idx)
            az = _get_float(row, cmap["az_rad"], row_idx, default=0.0)
            el = _get_float(row, cmap["el_rad"], row_idx, default=0.0)
            scenario = str(row.get(cmap["scenario_id"], "")).strip()
            rows.append((range_m, az, el, observed_amp, scenario))

    if len(rows) == 0:
        raise ValueError("CSV has no data rows")

    arr = np.asarray(rows, dtype=object)
    return {
        "range_m": np.asarray(arr[:, 0], dtype=np.float64),
        "az_rad": np.asarray(arr[:, 1], dtype=np.float64),
        "el_rad": np.asarray(arr[:, 2], dtype=np.float64),
        "observed_amp": np.asarray(arr[:, 3], dtype=np.float64),
        "scenario_id": np.asarray(arr[:, 4], dtype=str),
    }


def fit_path_power_parameters(
    range_m: np.ndarray,
    observed_amp: np.ndarray,
    model: str,
    az_rad: Optional[np.ndarray] = None,
    el_rad: Optional[np.ndarray] = None,
    p_t_dbm: float = 0.0,
    fc_hz: float = 77e9,
    pixel_width: int = 1,
    pixel_height: int = 1,
    grid: Optional[Mapping[str, Sequence[float]]] = None,
    top_k: int = 10,
) -> Dict[str, Any]:
    model_name = str(model).strip().lower()
    if model_name not in {"reflection", "scattering"}:
        raise ValueError("model must be reflection or scattering")

    r = np.asarray(range_m, dtype=np.float64).reshape(-1)
    obs = np.asarray(observed_amp, dtype=np.float64).reshape(-1)
    if r.size == 0:
        raise ValueError("range_m must be non-empty")
    if obs.size != r.size:
        raise ValueError("observed_amp size mismatch")
    if np.any(r <= 0):
        raise ValueError("range_m must be strictly positive")
    if np.any(obs <= 0):
        raise ValueError("observed_amp must be strictly positive")
    az, el = _resolve_angles(r.size, az_rad=az_rad, el_rad=el_rad)

    lambda_m = C0 / float(fc_hz)
    grid_use = dict(DEFAULT_REFLECTION_GRID if model_name == "reflection" else DEFAULT_SCATTERING_GRID)
    if grid is not None:
        for key, values in grid.items():
            grid_use[str(key)] = list(float(x) for x in values)

    candidates = _enumerate_grid(model_name, grid_use)
    if len(candidates) == 0:
        raise ValueError("grid produced zero candidates")

    rows = []
    for params in candidates:
        pred0 = _predict_with_params(
            model=model_name,
            params=params,
            range_m=r,
            az_rad=az,
            el_rad=el,
            p_t_dbm=float(p_t_dbm),
            lambda_m=float(lambda_m),
            pixel_width=int(pixel_width),
            pixel_height=int(pixel_height),
            gain_scale=1.0,
        )
        gain = _fit_gain_scale_log(obs, pred0)
        pred = np.maximum(pred0 * float(gain), np.finfo(np.float64).tiny)
        metrics = _error_metrics(obs, pred)
        row = {
            "params": dict(params, gain_scale=float(gain)),
            "metrics": metrics,
        }
        rows.append(row)

    ranked = sorted(rows, key=lambda x: float(x["metrics"]["rmse_log"]))
    best = ranked[0]
    return {
        "model": model_name,
        "sample_count": int(r.size),
        "fc_hz": float(fc_hz),
        "lambda_m": float(lambda_m),
        "p_t_dbm": float(p_t_dbm),
        "pixel_width": int(pixel_width),
        "pixel_height": int(pixel_height),
        "searched_candidates": int(len(candidates)),
        "best_params": best["params"],
        "best_metrics": best["metrics"],
        "top_candidates": ranked[: max(1, int(top_k))],
    }


def evaluate_path_power_parameters(
    range_m: np.ndarray,
    observed_amp: np.ndarray,
    model: str,
    params: Mapping[str, float],
    az_rad: Optional[np.ndarray] = None,
    el_rad: Optional[np.ndarray] = None,
    p_t_dbm: float = 0.0,
    fc_hz: float = 77e9,
    pixel_width: int = 1,
    pixel_height: int = 1,
) -> Dict[str, float]:
    model_name = str(model).strip().lower()
    if model_name not in {"reflection", "scattering"}:
        raise ValueError("model must be reflection or scattering")
    r = np.asarray(range_m, dtype=np.float64).reshape(-1)
    obs = np.asarray(observed_amp, dtype=np.float64).reshape(-1)
    if r.size == 0:
        raise ValueError("range_m must be non-empty")
    if obs.size != r.size:
        raise ValueError("observed_amp size mismatch")
    az, el = _resolve_angles(r.size, az_rad=az_rad, el_rad=el_rad)
    lambda_m = C0 / float(fc_hz)
    p = {str(k): float(v) for k, v in params.items()}
    gain_scale = float(p.get("gain_scale", 1.0))
    pred = _predict_with_params(
        model=model_name,
        params=p,
        range_m=r,
        az_rad=az,
        el_rad=el,
        p_t_dbm=float(p_t_dbm),
        lambda_m=float(lambda_m),
        pixel_width=int(pixel_width),
        pixel_height=int(pixel_height),
        gain_scale=float(gain_scale),
    )
    return _error_metrics(obs, pred)


def save_path_power_fit_json(out_json: str, payload: Mapping[str, Any]) -> None:
    Path(out_json).write_text(json.dumps(_to_jsonable(payload), indent=2), encoding="utf-8")


def load_column_map_json(path: str) -> Dict[str, str]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("column map JSON must be an object")
    return {str(k): str(v) for k, v in payload.items()}


def _resolve_angles(size: int, az_rad: Optional[np.ndarray], el_rad: Optional[np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
    if az_rad is None:
        az = np.zeros(size, dtype=np.float64)
    else:
        az = np.asarray(az_rad, dtype=np.float64).reshape(-1)
    if el_rad is None:
        el = np.zeros(size, dtype=np.float64)
    else:
        el = np.asarray(el_rad, dtype=np.float64).reshape(-1)
    if az.size != size or el.size != size:
        raise ValueError("az_rad/el_rad size mismatch")
    return az, el


def _enumerate_grid(model: str, grid: Mapping[str, Sequence[float]]) -> Sequence[Dict[str, float]]:
    if model == "reflection":
        out = []
        for rexp in _grid_list(grid, "range_power_exponent"):
            out.append({"range_power_exponent": float(rexp)})
        return out

    out = []
    for rexp in _grid_list(grid, "range_power_exponent"):
        for epow in _grid_list(grid, "elevation_power"):
            for amix in _grid_list(grid, "azimuth_mix"):
                for apow in _grid_list(grid, "azimuth_power"):
                    out.append(
                        {
                            "range_power_exponent": float(rexp),
                            "elevation_power": float(epow),
                            "azimuth_mix": float(amix),
                            "azimuth_power": float(apow),
                        }
                    )
    return out


def _grid_list(grid: Mapping[str, Sequence[float]], key: str) -> Sequence[float]:
    values = grid.get(key, None)
    if values is None:
        raise ValueError(f"grid missing key: {key}")
    arr = [float(x) for x in values]
    if len(arr) == 0:
        raise ValueError(f"grid key has empty list: {key}")
    return arr


def _predict_with_params(
    model: str,
    params: Mapping[str, float],
    range_m: np.ndarray,
    az_rad: np.ndarray,
    el_rad: np.ndarray,
    p_t_dbm: float,
    lambda_m: float,
    pixel_width: int,
    pixel_height: int,
    gain_scale: float,
) -> np.ndarray:
    r = np.asarray(range_m, dtype=np.float64).reshape(-1)
    if model == "reflection":
        return calculate_reflecting_path_power(
            p_t_dbm=float(p_t_dbm),
            pixel_width=int(pixel_width),
            pixel_height=int(pixel_height),
            reflecting_coefficient=1.0,
            lambda_m=float(lambda_m),
            temp_range_m=r,
            range_power_exponent=float(params.get("range_power_exponent", 4.0)),
            gain_scale=float(gain_scale),
        )

    ang = np.stack([az_rad, el_rad], axis=1)
    return calculate_scattering_path_power(
        p_t_dbm=float(p_t_dbm),
        pixel_width=int(pixel_width),
        pixel_height=int(pixel_height),
        scattering_coefficient=1.0,
        lambda_m=float(lambda_m),
        temp_range_m=r,
        temp_angles_rad=ang,
        range_power_exponent=float(params.get("range_power_exponent", 4.0)),
        gain_scale=float(gain_scale),
        elevation_power=float(params.get("elevation_power", 2.0)),
        azimuth_mix=float(params.get("azimuth_mix", 0.6)),
        azimuth_power=float(params.get("azimuth_power", 2.0)),
    )


def _fit_gain_scale_log(observed_amp: np.ndarray, pred_nominal_amp: np.ndarray) -> float:
    eps = np.finfo(np.float64).tiny
    y = np.log(np.maximum(np.asarray(observed_amp, dtype=np.float64), eps))
    x = np.log(np.maximum(np.asarray(pred_nominal_amp, dtype=np.float64), eps))
    return float(np.exp(np.mean(y - x)))


def _error_metrics(observed_amp: np.ndarray, pred_amp: np.ndarray) -> Dict[str, float]:
    eps = np.finfo(np.float64).tiny
    obs = np.maximum(np.asarray(observed_amp, dtype=np.float64), eps)
    pred = np.maximum(np.asarray(pred_amp, dtype=np.float64), eps)
    diff = pred - obs
    log_diff = np.log(pred) - np.log(obs)
    corr = _corrcoef(obs, pred)
    return {
        "rmse_linear": float(np.sqrt(np.mean(diff**2))),
        "mae_linear": float(np.mean(np.abs(diff))),
        "rmse_log": float(np.sqrt(np.mean(log_diff**2))),
        "mae_log": float(np.mean(np.abs(log_diff))),
        "mape": float(np.mean(np.abs(diff) / np.maximum(obs, eps))),
        "corrcoef_linear": float(corr),
    }


def _validate_required(fieldnames: Sequence[str], keys: Sequence[str], cmap: Mapping[str, str]) -> None:
    present = set(str(x) for x in fieldnames)
    missing = []
    for key in keys:
        col = cmap.get(key, key)
        if col not in present:
            missing.append(f"{key}->{col}")
    if missing:
        raise ValueError("missing required CSV columns: " + ", ".join(missing))


def _get_float(row: Mapping[str, Any], col: str, row_idx: int, default: Optional[float] = None) -> float:
    raw = row.get(col, None)
    if raw is None or str(raw).strip() == "":
        if default is not None:
            return float(default)
        raise ValueError(f"empty value at row {row_idx}, column {col}")
    try:
        return float(str(raw).strip())
    except ValueError as exc:
        raise ValueError(f"invalid float at row {row_idx}, column {col}: {raw}") from exc


def _corrcoef(x: np.ndarray, y: np.ndarray) -> float:
    x0 = np.asarray(x, dtype=np.float64).reshape(-1)
    y0 = np.asarray(y, dtype=np.float64).reshape(-1)
    if x0.size <= 1:
        return 1.0
    xv = x0 - float(np.mean(x0))
    yv = y0 - float(np.mean(y0))
    den = np.sqrt(np.sum(xv**2) * np.sum(yv**2)) + 1e-12
    return float(np.sum(xv * yv) / den)


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value
