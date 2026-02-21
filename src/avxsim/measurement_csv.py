import csv
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import numpy as np

from .calibration_samples import save_calibration_samples_npz


DEFAULT_MEASUREMENT_COLUMN_MAP: Dict[str, str] = {
    "tx_theta_re": "tx_theta_re",
    "tx_theta_im": "tx_theta_im",
    "tx_phi_re": "tx_phi_re",
    "tx_phi_im": "tx_phi_im",
    "rx_theta_re": "rx_theta_re",
    "rx_theta_im": "rx_theta_im",
    "rx_phi_re": "rx_phi_re",
    "rx_phi_im": "rx_phi_im",
    "observed_re": "observed_re",
    "observed_im": "observed_im",
    "path_m00_re": "path_m00_re",
    "path_m00_im": "path_m00_im",
    "path_m01_re": "path_m01_re",
    "path_m01_im": "path_m01_im",
    "path_m10_re": "path_m10_re",
    "path_m10_im": "path_m10_im",
    "path_m11_re": "path_m11_re",
    "path_m11_im": "path_m11_im",
    "chirp_idx": "chirp_idx",
    "tx_idx": "tx_idx",
    "rx_idx": "rx_idx",
    "path_idx": "path_idx",
    "frame_idx": "frame_idx",
}


def build_calibration_samples_from_measurement_csv(
    csv_path: str,
    column_map: Optional[Mapping[str, str]] = None,
    delimiter: str = ",",
) -> Dict[str, np.ndarray]:
    """
    Convert measured CSV rows to calibration sample arrays.

    Required canonical keys:
      tx_theta_re, tx_theta_im, tx_phi_re, tx_phi_im,
      rx_theta_re, rx_theta_im, rx_phi_re, rx_phi_im,
      observed_re, observed_im

    Optional canonical keys:
      path_m00_re, path_m00_im, path_m01_re, path_m01_im,
      path_m10_re, path_m10_im, path_m11_re, path_m11_im
      chirp_idx, tx_idx, rx_idx, path_idx, frame_idx
    """
    cmap = dict(DEFAULT_MEASUREMENT_COLUMN_MAP)
    if column_map is not None:
        for key, value in column_map.items():
            cmap[str(key)] = str(value)

    required = [
        "tx_theta_re",
        "tx_theta_im",
        "tx_phi_re",
        "tx_phi_im",
        "rx_theta_re",
        "rx_theta_im",
        "rx_phi_re",
        "rx_phi_im",
        "observed_re",
        "observed_im",
    ]
    path_keys = [
        "path_m00_re",
        "path_m00_im",
        "path_m01_re",
        "path_m01_im",
        "path_m10_re",
        "path_m10_im",
        "path_m11_re",
        "path_m11_im",
    ]
    optional_index_keys = ["chirp_idx", "tx_idx", "rx_idx", "path_idx", "frame_idx"]

    tx_jones = []
    rx_jones = []
    observed = []
    path_matrices = []
    idx_buffers: Dict[str, list] = {k: [] for k in optional_index_keys}
    has_index: Dict[str, bool] = {k: False for k in optional_index_keys}

    with Path(csv_path).open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("CSV must contain a header row")
        _validate_required_columns(reader.fieldnames, required, cmap)
        path_presence = _path_matrix_presence(reader.fieldnames, path_keys, cmap)

        row_count = 0
        for row_idx, row in enumerate(reader, start=2):
            row_count += 1
            tx_t = complex(_get_float(row, cmap["tx_theta_re"], row_idx), _get_float(row, cmap["tx_theta_im"], row_idx))
            tx_p = complex(_get_float(row, cmap["tx_phi_re"], row_idx), _get_float(row, cmap["tx_phi_im"], row_idx))
            rx_t = complex(_get_float(row, cmap["rx_theta_re"], row_idx), _get_float(row, cmap["rx_theta_im"], row_idx))
            rx_p = complex(_get_float(row, cmap["rx_phi_re"], row_idx), _get_float(row, cmap["rx_phi_im"], row_idx))
            obs = complex(_get_float(row, cmap["observed_re"], row_idx), _get_float(row, cmap["observed_im"], row_idx))

            if path_presence:
                p00 = complex(_get_float(row, cmap["path_m00_re"], row_idx), _get_float(row, cmap["path_m00_im"], row_idx))
                p01 = complex(_get_float(row, cmap["path_m01_re"], row_idx), _get_float(row, cmap["path_m01_im"], row_idx))
                p10 = complex(_get_float(row, cmap["path_m10_re"], row_idx), _get_float(row, cmap["path_m10_im"], row_idx))
                p11 = complex(_get_float(row, cmap["path_m11_re"], row_idx), _get_float(row, cmap["path_m11_im"], row_idx))
                pmat = np.asarray([[p00, p01], [p10, p11]], dtype=np.complex128)
            else:
                pmat = np.eye(2, dtype=np.complex128)

            tx_jones.append(np.asarray([tx_t, tx_p], dtype=np.complex128))
            rx_jones.append(np.asarray([rx_t, rx_p], dtype=np.complex128))
            observed.append(obs)
            path_matrices.append(pmat)

            for key in optional_index_keys:
                col = cmap.get(key, key)
                if col in row and str(row[col]).strip() != "":
                    has_index[key] = True
                    idx_buffers[key].append(int(float(row[col])))
                else:
                    idx_buffers[key].append(0)

    if row_count <= 0:
        raise ValueError("CSV has no data rows")

    out: Dict[str, np.ndarray] = {
        "tx_jones": np.asarray(tx_jones, dtype=np.complex128),
        "rx_jones": np.asarray(rx_jones, dtype=np.complex128),
        "observed_gain": np.asarray(observed, dtype=np.complex128),
        "path_matrices": np.asarray(path_matrices, dtype=np.complex128),
    }
    for key in optional_index_keys:
        if has_index[key]:
            out[key] = np.asarray(idx_buffers[key], dtype=np.int64)
    return out


def convert_measurement_csv_to_npz(
    csv_path: str,
    out_npz: str,
    column_map: Optional[Mapping[str, str]] = None,
    delimiter: str = ",",
) -> Dict[str, np.ndarray]:
    samples = build_calibration_samples_from_measurement_csv(
        csv_path=csv_path,
        column_map=column_map,
        delimiter=delimiter,
    )
    metadata = {
        "source_csv": str(Path(csv_path)),
        "delimiter": str(delimiter),
        "column_map": _jsonable_mapping(column_map) if column_map is not None else {},
    }
    save_calibration_samples_npz(out_npz=out_npz, samples=samples, metadata=metadata)
    return samples


def load_column_map_json(path: str) -> Dict[str, str]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("column map JSON must be an object")
    out: Dict[str, str] = {}
    for key, value in payload.items():
        out[str(key)] = str(value)
    return out


def _validate_required_columns(fieldnames, required, cmap) -> None:
    present = set(str(x) for x in fieldnames)
    missing = []
    for key in required:
        col = cmap.get(key, key)
        if col not in present:
            missing.append(f"{key}->{col}")
    if missing:
        raise ValueError("missing required CSV columns: " + ", ".join(missing))


def _path_matrix_presence(fieldnames, path_keys, cmap) -> bool:
    present = set(str(x) for x in fieldnames)
    present_flags = []
    for key in path_keys:
        col = cmap.get(key, key)
        present_flags.append(col in present)
    n_present = int(sum(1 for x in present_flags if x))
    if n_present == 0:
        return False
    if n_present != len(path_keys):
        raise ValueError("path matrix columns must be either all present or all absent")
    return True


def _get_float(row: Mapping[str, Any], col: str, row_idx: int) -> float:
    if col not in row:
        raise ValueError(f"missing column at row {row_idx}: {col}")
    raw = str(row[col]).strip()
    if raw == "":
        raise ValueError(f"empty value at row {row_idx}, column {col}")
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"invalid float at row {row_idx}, column {col}: {raw}") from exc


def _jsonable_mapping(value: Mapping[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, item in value.items():
        out[str(key)] = str(item)
    return out

