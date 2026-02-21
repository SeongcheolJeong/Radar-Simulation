import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .parity import DEFAULT_PARITY_THRESHOLDS
from .replay_manifest_builder import (
    build_replay_manifest_case,
    build_replay_manifest_payload,
    save_replay_manifest_json,
)
from .scenario_profile import build_scenario_profile_payload, save_scenario_profile_json


DEFAULT_ADC_ORDER = "sctr"
DEFAULT_ADC_KEY = "adc"


def reorder_adc_to_sctr(adc: np.ndarray, adc_order: str = DEFAULT_ADC_ORDER) -> np.ndarray:
    order = str(adc_order).lower().strip()
    if len(order) != 4 or set(order) != {"s", "c", "t", "r"}:
        raise ValueError("adc_order must be permutation of s,c,t,r (e.g., sctr, scrt)")

    arr = np.asarray(adc)
    if arr.ndim != 4:
        raise ValueError("adc must be 4D")

    perm = [order.index("s"), order.index("c"), order.index("t"), order.index("r")]
    out = np.transpose(arr, axes=perm)
    if not np.iscomplexobj(out):
        out = out.astype(np.float64)
    return out


def load_adc_from_npz(npz_path: str, adc_key: str = DEFAULT_ADC_KEY) -> Tuple[np.ndarray, Dict[str, Any]]:
    path = Path(npz_path)
    if not path.exists():
        raise FileNotFoundError(str(path))

    with np.load(str(path), allow_pickle=False) as payload:
        keys = list(payload.files)
        arr = None
        chosen_key = None

        if adc_key in payload:
            arr = np.asarray(payload[adc_key])
            chosen_key = str(adc_key)
        else:
            for key in keys:
                v = np.asarray(payload[key])
                if v.ndim == 4:
                    arr = v
                    chosen_key = str(key)
                    break

        if arr is None:
            raise ValueError(f"npz has no 4D adc array: {npz_path}")

        meta: Dict[str, Any] = {
            "npz_path": str(path),
            "adc_key": chosen_key,
            "keys": keys,
            "shape": list(arr.shape),
            "dtype": str(arr.dtype),
        }

        if "metadata_json" in payload:
            try:
                meta["metadata_json"] = json.loads(str(payload["metadata_json"].tolist()))
            except Exception:
                meta["metadata_json"] = str(payload["metadata_json"])

    return arr, meta


def estimate_rd_ra_from_adc(
    adc_sctr: np.ndarray,
    nfft_range: Optional[int] = None,
    nfft_doppler: Optional[int] = None,
    nfft_angle: Optional[int] = None,
    range_window: str = "hann",
    doppler_window: str = "hann",
    angle_window: str = "hann",
    range_bin_limit: Optional[int] = None,
) -> Dict[str, np.ndarray]:
    adc = np.asarray(adc_sctr)
    if adc.ndim != 4:
        raise ValueError("adc_sctr must be 4D [sample, chirp, tx, rx]")

    n_samp, n_chirp, n_tx, n_rx = adc.shape
    if n_samp <= 0 or n_chirp <= 0 or n_tx <= 0 or n_rx <= 0:
        raise ValueError("invalid adc shape")

    nr = int(n_samp) if nfft_range is None else int(nfft_range)
    nd = int(n_chirp) if nfft_doppler is None else int(nfft_doppler)
    na = int(n_tx * n_rx) if nfft_angle is None else int(nfft_angle)
    if nr <= 0 or nd <= 0 or na <= 0:
        raise ValueError("FFT sizes must be positive")

    wr = _window(int(n_samp), range_window).reshape(-1, 1, 1, 1)
    wd = _window(int(n_chirp), doppler_window).reshape(1, -1, 1, 1)
    wa = _window(int(n_tx * n_rx), angle_window).reshape(-1, 1)

    rng = np.fft.fft(adc * wr, n=nr, axis=0)
    n_range = nr // 2
    if n_range <= 0:
        raise ValueError("nfft_range too small")
    rng = rng[:n_range, :, :, :]

    if range_bin_limit is not None:
        n_keep = int(range_bin_limit)
        if n_keep <= 0:
            raise ValueError("range_bin_limit must be positive when set")
        rng = rng[: min(n_keep, rng.shape[0]), :, :, :]

    dop = np.fft.fftshift(np.fft.fft(rng * wd, n=nd, axis=1), axes=1)
    rd = np.mean(np.abs(dop) ** 2, axis=(2, 3)).T

    snap = np.mean(rng, axis=1)
    virt = snap.reshape(snap.shape[0], n_tx * n_rx).T
    ang = np.fft.fftshift(np.fft.fft(virt * wa, n=na, axis=0), axes=0)
    ra = np.abs(ang) ** 2

    tiny = np.finfo(np.float64).tiny
    rd = np.maximum(np.asarray(rd, dtype=np.float64), tiny)
    ra = np.maximum(np.asarray(ra, dtype=np.float64), tiny)

    return {
        "fx_dop_win": rd,
        "fx_ang": ra,
        "metadata": {
            "input_shape_sctr": [int(x) for x in adc.shape],
            "nfft_range": int(nr),
            "nfft_doppler": int(nd),
            "nfft_angle": int(na),
            "range_window": str(range_window),
            "doppler_window": str(doppler_window),
            "angle_window": str(angle_window),
            "range_bin_limit": None if range_bin_limit is None else int(range_bin_limit),
        },
    }


def build_measured_pack_from_adc_npz(
    adc_npz_files: Sequence[str],
    output_pack_root: str,
    scenario_id: str,
    adc_order: str = DEFAULT_ADC_ORDER,
    adc_key: str = DEFAULT_ADC_KEY,
    reference_index: int = 0,
    nfft_range: Optional[int] = None,
    nfft_doppler: Optional[int] = None,
    nfft_angle: Optional[int] = None,
    range_window: str = "hann",
    doppler_window: str = "hann",
    angle_window: str = "hann",
    range_bin_limit: Optional[int] = None,
    include_candidate_metadata: bool = True,
) -> Dict[str, Any]:
    if len(adc_npz_files) == 0:
        raise ValueError("adc_npz_files must be non-empty")

    out_root = Path(output_pack_root)
    if out_root.exists() and any(out_root.iterdir()):
        raise ValueError(f"output pack root exists and is not empty: {out_root}")
    out_root.mkdir(parents=True, exist_ok=True)

    cand_dir = out_root / "candidates"
    cand_dir.mkdir(parents=True, exist_ok=True)

    candidate_rows: List[Dict[str, Any]] = []
    for i, src in enumerate(adc_npz_files):
        adc_raw, meta = load_adc_from_npz(src, adc_key=adc_key)
        adc_sctr = reorder_adc_to_sctr(adc_raw, adc_order=adc_order)
        est = estimate_rd_ra_from_adc(
            adc_sctr=adc_sctr,
            nfft_range=nfft_range,
            nfft_doppler=nfft_doppler,
            nfft_angle=nfft_angle,
            range_window=range_window,
            doppler_window=doppler_window,
            angle_window=angle_window,
            range_bin_limit=range_bin_limit,
        )

        base = Path(src).stem
        out_npz = cand_dir / f"{i:04d}_{base}.npz"
        np.savez_compressed(
            str(out_npz),
            fx_dop_win=est["fx_dop_win"],
            fx_ang=est["fx_ang"],
            metadata_json=json.dumps(
                {
                    "source_adc_npz": str(src),
                    "adc_order": str(adc_order),
                    "adc_key": str(meta.get("adc_key")),
                    "adc_shape": list(np.asarray(adc_sctr).shape),
                    "estimation": est["metadata"],
                }
            ),
        )

        row = {
            "name": f"cand_{i:04d}_{base}",
            "estimation_npz": str(out_npz),
        }
        if include_candidate_metadata:
            row["metadata"] = {
                "source_adc_npz": str(src),
                "adc_info": meta,
                "estimation": est["metadata"],
            }
        candidate_rows.append(row)

    ref_idx = int(reference_index)
    if ref_idx < 0 or ref_idx >= len(candidate_rows):
        raise ValueError("reference_index out of range")
    reference_npz = candidate_rows[ref_idx]["estimation_npz"]

    profile_json = out_root / "scenario_profile.json"
    profile = build_scenario_profile_payload(
        scenario_id=str(scenario_id),
        global_jones_matrix=np.eye(2, dtype=np.complex128),
        parity_thresholds=dict(DEFAULT_PARITY_THRESHOLDS),
        reference_estimation_npz=str(reference_npz),
        motion_compensation_defaults={
            "enabled": False,
            "fd_hz": None,
            "chirp_interval_s": None,
            "reference_tx": None,
        },
    )
    save_scenario_profile_json(str(profile_json), profile)

    lock_policy_json = out_root / "lock_policy.json"
    lock_policy_json.write_text(
        json.dumps(
            {
                "min_pass_rate": 1.0,
                "max_case_fail_count": 0,
                "require_motion_defaults_enabled": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    case = build_replay_manifest_case(
        pack_root=str(out_root),
        scenario_id=str(scenario_id),
        profile_json=str(profile_json),
        candidate_paths=[str(x["estimation_npz"]) for x in candidate_rows],
        reference_estimation_npz=None,
        include_sidecar_metadata=False,
        candidate_name_mode="stem",
    )
    case["candidates"] = candidate_rows

    replay_manifest_json = out_root / "replay_manifest.json"
    save_replay_manifest_json(
        str(replay_manifest_json),
        build_replay_manifest_payload([case]),
    )

    return {
        "output_pack_root": str(out_root),
        "scenario_id": str(scenario_id),
        "candidate_count": int(len(candidate_rows)),
        "reference_index": int(ref_idx),
        "reference_estimation_npz": str(reference_npz),
        "profile_json": str(profile_json),
        "replay_manifest_json": str(replay_manifest_json),
        "lock_policy_json": str(lock_policy_json),
    }


def _window(length: int, kind: str) -> np.ndarray:
    n = int(length)
    if n <= 0:
        raise ValueError("window length must be positive")
    k = str(kind).lower().strip()
    if k in {"", "none", "rect", "boxcar"}:
        return np.ones(n, dtype=np.float64)
    if k == "hann":
        return np.hanning(n).astype(np.float64)
    if k == "hamming":
        return np.hamming(n).astype(np.float64)
    raise ValueError(f"unsupported window kind: {kind}")
