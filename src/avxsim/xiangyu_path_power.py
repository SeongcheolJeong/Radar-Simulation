import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .adc_pack_builder import estimate_rd_ra_from_adc, load_adc_from_npz, reorder_adc_to_sctr
from .mat_adc_extract import load_adc_from_mat


def load_xiangyu_label_rows(label_csv_path: str) -> List[Dict[str, Any]]:
    path = Path(label_csv_path)
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 6:
                continue
            try:
                rows.append(
                    {
                        "uid": int(float(row[0])),
                        "class_id": int(float(row[1])),
                        "px_m": float(row[2]),
                        "py_m": float(row[3]),
                        "wid_m": float(row[4]),
                        "len_m": float(row[5]),
                    }
                )
            except Exception:
                continue
    return rows


def build_path_power_samples_from_xiangyu_sequence(
    adc_root_dir: str,
    labels_root_dir: str,
    scenario_id: Optional[str] = None,
    adc_type: str = "mat",
    adc_glob: Optional[str] = None,
    labels_glob: str = "*.csv",
    adc_key: str = "adc",
    adc_order: str = "scrt",
    mat_variable: Optional[str] = None,
    max_frames: Optional[int] = None,
    stride: int = 1,
    min_py_m: float = 0.0,
    distance_limits_m: Tuple[float, float] = (0.0, 100.0),
    range_max_m: float = 30.0,
    nfft_range: Optional[int] = None,
    nfft_doppler: Optional[int] = None,
    nfft_angle: Optional[int] = None,
    range_window: str = "hann",
    doppler_window: str = "hann",
    angle_window: str = "hann",
    range_bin_limit: Optional[int] = None,
    bin_search_radius: int = 1,
) -> Dict[str, Any]:
    adc_mode = str(adc_type).strip().lower()
    if adc_mode not in {"mat", "npz"}:
        raise ValueError("adc_type must be mat or npz")
    if int(stride) <= 0:
        raise ValueError("stride must be positive")
    if float(range_max_m) <= 0:
        raise ValueError("range_max_m must be positive")
    if int(bin_search_radius) < 0:
        raise ValueError("bin_search_radius must be >= 0")

    adc_root = Path(adc_root_dir)
    labels_root = Path(labels_root_dir)
    if not adc_root.exists() or not adc_root.is_dir():
        raise ValueError(f"adc_root_dir must be existing directory: {adc_root}")
    if not labels_root.exists() or not labels_root.is_dir():
        raise ValueError(f"labels_root_dir must be existing directory: {labels_root}")

    if adc_glob is None:
        adc_glob = "*.mat" if adc_mode == "mat" else "*.npz"

    adc_files = sorted([p for p in adc_root.glob(str(adc_glob)) if p.is_file()])
    label_files = sorted([p for p in labels_root.glob(str(labels_glob)) if p.is_file()])
    if len(adc_files) == 0:
        raise ValueError(f"no ADC files found in {adc_root} with glob {adc_glob}")
    if len(label_files) == 0:
        raise ValueError(f"no label CSV files found in {labels_root} with glob {labels_glob}")

    adc_by_idx = _index_file_map(adc_files)
    labels_by_idx = _index_file_map(label_files)
    matched_indices = sorted(set(adc_by_idx.keys()) & set(labels_by_idx.keys()))
    matched_indices = matched_indices[:: int(stride)]
    if max_frames is not None:
        matched_indices = matched_indices[: int(max_frames)]
    if len(matched_indices) == 0:
        raise ValueError("no matched frame indices between ADC and labels")

    sid = str(scenario_id) if scenario_id is not None else labels_root.parent.name

    rows: List[Dict[str, Any]] = []
    frame_count = 0
    label_count = 0
    selected_count = 0

    for k, frame_index in enumerate(matched_indices):
        adc_path = adc_by_idx[frame_index]
        label_path = labels_by_idx[frame_index]
        label_rows = load_xiangyu_label_rows(str(label_path))
        if len(label_rows) == 0:
            continue

        adc_raw = _load_adc_array(
            path=str(adc_path),
            adc_mode=adc_mode,
            adc_key=str(adc_key),
            mat_variable=mat_variable,
        )
        adc_sctr = reorder_adc_to_sctr(adc_raw, adc_order=str(adc_order))
        est = estimate_rd_ra_from_adc(
            adc_sctr=adc_sctr,
            nfft_range=nfft_range,
            nfft_doppler=nfft_doppler,
            nfft_angle=nfft_angle,
            range_window=str(range_window),
            doppler_window=str(doppler_window),
            angle_window=str(angle_window),
            range_bin_limit=range_bin_limit,
        )
        ra = np.asarray(est["fx_ang"], dtype=np.float64)
        if ra.ndim != 2:
            raise ValueError("fx_ang must be 2D")
        n_ang, n_rng = ra.shape

        frame_count += 1
        for path_idx, item in enumerate(label_rows):
            label_count += 1
            px = float(item["px_m"])
            py = float(item["py_m"])
            if py < float(min_py_m):
                continue
            range_m = float(np.hypot(px, py))
            dmin, dmax = float(distance_limits_m[0]), float(distance_limits_m[1])
            if not (dmin <= range_m <= dmax):
                continue

            az = float(np.arctan2(px, py))
            el = 0.0
            rbin = int(np.clip(np.rint((range_m / float(range_max_m)) * (n_rng - 1)), 0, n_rng - 1))
            abin = _azimuth_to_angle_bin(az_rad=az, n_angle_bins=n_ang)

            amp = _pick_amplitude(
                ra_power=ra,
                angle_bin=abin,
                range_bin=rbin,
                radius=int(bin_search_radius),
            )
            if amp <= 0:
                continue

            row = {
                "scenario_id": str(sid),
                "chirp_idx": int(k),
                "path_idx": int(path_idx),
                "frame_idx": int(frame_index),
                "range_m": float(range_m),
                "az_rad": float(az),
                "el_rad": float(el),
                "observed_amp": float(amp),
                "uid": int(item["uid"]),
                "class_id": int(item["class_id"]),
                "px_m": float(px),
                "py_m": float(py),
                "wid_m": float(item["wid_m"]),
                "len_m": float(item["len_m"]),
                "range_bin": int(rbin),
                "angle_bin": int(abin),
                "adc_file": str(adc_path),
                "label_file": str(label_path),
            }
            rows.append(row)
            selected_count += 1

    if len(rows) == 0:
        raise ValueError("no path-power rows selected")

    return {
        "rows": rows,
        "metadata": {
            "scenario_id": str(sid),
            "adc_type": str(adc_mode),
            "adc_root_dir": str(adc_root),
            "labels_root_dir": str(labels_root),
            "matched_frame_count": int(len(matched_indices)),
            "processed_frame_count": int(frame_count),
            "raw_label_count": int(label_count),
            "selected_row_count": int(selected_count),
            "adc_order": str(adc_order),
            "range_max_m": float(range_max_m),
            "distance_limits_m": [float(distance_limits_m[0]), float(distance_limits_m[1])],
            "min_py_m": float(min_py_m),
            "bin_search_radius": int(bin_search_radius),
            "nfft_range": None if nfft_range is None else int(nfft_range),
            "nfft_doppler": None if nfft_doppler is None else int(nfft_doppler),
            "nfft_angle": None if nfft_angle is None else int(nfft_angle),
            "range_bin_limit": None if range_bin_limit is None else int(range_bin_limit),
        },
    }


def save_path_power_rows_csv(output_csv: str, rows: Sequence[Mapping[str, Any]]) -> None:
    out = Path(output_csv)
    out.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "scenario_id",
        "chirp_idx",
        "path_idx",
        "frame_idx",
        "range_m",
        "az_rad",
        "el_rad",
        "observed_amp",
        "uid",
        "class_id",
        "px_m",
        "py_m",
        "wid_m",
        "len_m",
        "range_bin",
        "angle_bin",
        "adc_file",
        "label_file",
    ]

    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in columns})


def _index_file_map(files: Sequence[Path]) -> Dict[int, Path]:
    out: Dict[int, Path] = {}
    for p in files:
        idx = _extract_numeric_index(p.stem)
        if idx is None:
            continue
        out.setdefault(int(idx), p)
    return out


def _extract_numeric_index(stem: str) -> Optional[int]:
    m = re.search(r"(\d+)$", str(stem))
    if m is None:
        return None
    return int(m.group(1))


def _load_adc_array(path: str, adc_mode: str, adc_key: str, mat_variable: Optional[str]) -> np.ndarray:
    if adc_mode == "mat":
        arr, _ = load_adc_from_mat(path=path, variable=mat_variable)
        return np.asarray(arr)
    arr, _ = load_adc_from_npz(npz_path=path, adc_key=adc_key)
    return np.asarray(arr)


def _azimuth_to_angle_bin(az_rad: float, n_angle_bins: int) -> int:
    # ULA angle bins are approximately linear in sin(theta), not theta.
    s = float(np.sin(float(az_rad)))
    idx = int(np.rint(((s + 1.0) * 0.5) * (int(n_angle_bins) - 1)))
    return int(np.clip(idx, 0, int(n_angle_bins) - 1))


def _pick_amplitude(ra_power: np.ndarray, angle_bin: int, range_bin: int, radius: int) -> float:
    ang0 = max(0, int(angle_bin) - int(radius))
    ang1 = min(int(ra_power.shape[0]), int(angle_bin) + int(radius) + 1)
    rng0 = max(0, int(range_bin) - int(radius))
    rng1 = min(int(ra_power.shape[1]), int(range_bin) + int(radius) + 1)
    patch = np.asarray(ra_power[ang0:ang1, rng0:rng1], dtype=np.float64)
    if patch.size == 0:
        return 0.0
    pmax = float(np.nanmax(np.maximum(patch, np.finfo(np.float64).tiny)))
    return float(np.sqrt(max(pmax, np.finfo(np.float64).tiny)))
