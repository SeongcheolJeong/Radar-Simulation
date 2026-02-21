import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .parity import DEFAULT_PARITY_THRESHOLDS
from .path_power_tuning import load_path_power_fit_json
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


def apply_path_power_fit_proxy_to_estimation(
    fx_dop_win: np.ndarray,
    fx_ang: np.ndarray,
    fit_payload: Mapping[str, Any],
) -> Dict[str, Any]:
    rd = np.asarray(fx_dop_win, dtype=np.float64)
    ra = np.asarray(fx_ang, dtype=np.float64)
    if rd.ndim != 2 or ra.ndim != 2:
        raise ValueError("fx_dop_win/fx_ang must be 2D")
    if rd.shape[1] != ra.shape[1]:
        raise ValueError("range-bin dimension must match between RD/RA")

    fit = fit_payload.get("fit", None)
    if not isinstance(fit, Mapping):
        raise ValueError("fit payload missing fit object")
    model = str(fit.get("model", "")).strip().lower()
    if model not in {"reflection", "scattering"}:
        raise ValueError("fit.model must be reflection or scattering")
    params = fit.get("best_params", {})
    if not isinstance(params, Mapping):
        raise ValueError("fit.best_params must be object")

    n_range = int(rd.shape[1])
    n_angle = int(ra.shape[0])
    tiny = float(np.finfo(np.float64).tiny)

    # Range proxy: compact dynamic span [1, 2] to avoid numeric blow-ups on large exponents.
    r = 1.0 + np.linspace(0.0, 1.0, num=n_range, dtype=np.float64)
    range_exp = max(float(params.get("range_power_exponent", 4.0)), 0.0)
    wr = np.power(np.maximum(r, tiny), -range_exp)
    wr = _normalize_weight(wr)

    wa = np.ones(n_angle, dtype=np.float64)
    if model == "scattering":
        az = np.linspace(-np.pi / 2.0, np.pi / 2.0, num=n_angle, dtype=np.float64)
        az_mix = float(np.clip(float(params.get("azimuth_mix", 0.6)), 0.0, 1.0))
        az_pow = max(float(params.get("azimuth_power", 2.0)), 0.0)
        front = np.power(np.maximum(np.abs(np.cos(az)), tiny), az_pow)
        side = np.power(np.maximum(np.abs(np.sin(az)), tiny), az_pow)
        wa = _normalize_weight((az_mix * front) + ((1.0 - az_mix) * side))

    rd_out = np.maximum(rd * wr[None, :], tiny)
    ra_out = np.maximum(ra * (wa[:, None] * wr[None, :]), tiny)
    return {
        "fx_dop_win": rd_out,
        "fx_ang": ra_out,
        "metadata": {
            "enabled": True,
            "fit_model": model,
            "best_params": {str(k): float(v) for k, v in params.items()},
            "range_weight_min": float(np.min(wr)),
            "range_weight_max": float(np.max(wr)),
            "angle_weight_min": float(np.min(wa)),
            "angle_weight_max": float(np.max(wa)),
            "note": "proxy weighting on RD/RA maps for measured-pack fit sensitivity",
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
    path_power_fit_json: Optional[str] = None,
) -> Dict[str, Any]:
    if len(adc_npz_files) == 0:
        raise ValueError("adc_npz_files must be non-empty")

    out_root = Path(output_pack_root)
    if out_root.exists() and any(out_root.iterdir()):
        raise ValueError(f"output pack root exists and is not empty: {out_root}")
    out_root.mkdir(parents=True, exist_ok=True)

    cand_dir = out_root / "candidates"
    cand_dir.mkdir(parents=True, exist_ok=True)

    fit_payload = (
        None if path_power_fit_json is None else load_path_power_fit_json(str(path_power_fit_json))
    )

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
        fit_proxy_meta = None
        if fit_payload is not None:
            shaped = apply_path_power_fit_proxy_to_estimation(
                fx_dop_win=est["fx_dop_win"],
                fx_ang=est["fx_ang"],
                fit_payload=fit_payload,
            )
            est["fx_dop_win"] = np.asarray(shaped["fx_dop_win"], dtype=np.float64)
            est["fx_ang"] = np.asarray(shaped["fx_ang"], dtype=np.float64)
            fit_proxy_meta = dict(shaped["metadata"])
            fit_proxy_meta["fit_json"] = str(path_power_fit_json)

        base = Path(src).stem
        out_npz = cand_dir / f"{i:04d}_{base}.npz"
        meta_json = {
            "source_adc_npz": str(src),
            "adc_order": str(adc_order),
            "adc_key": str(meta.get("adc_key")),
            "adc_shape": list(np.asarray(adc_sctr).shape),
            "estimation": est["metadata"],
        }
        if fit_proxy_meta is not None:
            meta_json["path_power_fit_proxy"] = fit_proxy_meta
        np.savez_compressed(
            str(out_npz),
            fx_dop_win=est["fx_dop_win"],
            fx_ang=est["fx_ang"],
            metadata_json=json.dumps(meta_json),
        )

        row = {
            "name": f"cand_{i:04d}_{base}",
            "estimation_npz": str(out_npz),
        }
        if include_candidate_metadata:
            row_meta = {
                "source_adc_npz": str(src),
                "adc_info": meta,
                "estimation": est["metadata"],
            }
            if fit_proxy_meta is not None:
                row_meta["path_power_fit_proxy"] = fit_proxy_meta
            row["metadata"] = row_meta
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
        "path_power_fit_json": None if path_power_fit_json is None else str(path_power_fit_json),
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


def _normalize_weight(w: np.ndarray) -> np.ndarray:
    arr = np.maximum(np.asarray(w, dtype=np.float64), np.finfo(np.float64).tiny)
    norm = float(np.median(arr))
    if not np.isfinite(norm) or norm <= 0.0:
        norm = float(np.mean(arr))
    if not np.isfinite(norm) or norm <= 0.0:
        norm = 1.0
    return arr / norm
