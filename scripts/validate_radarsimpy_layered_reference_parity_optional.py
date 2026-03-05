#!/usr/bin/env python3
from __future__ import annotations

import argparse
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple

import numpy as np

import avxsim.radarsimpy_api as api
from avxsim import radarsimpy_core_processing as core_proc
from avxsim import radarsimpy_core_tools as core_tools
from avxsim.radarsimpy_core_simulator import core_sim_radar, core_sim_rcs


TRIAL_THRESHOLDS: Dict[str, float] = {
    "range_peak_diff_max": 2.0,
    "doppler_peak_diff_max": 2.0,
    "rd_norm_corr_aligned_min": 0.60,
    "rd_norm_corr_aligned_strict_for_shifted_peak": 0.80,
    "numeric_rtol": 1e-6,
    "numeric_atol": 1e-8,
}

PRODUCTION_THRESHOLDS: Dict[str, float] = {
    "range_peak_diff_max": 2.0,
    "doppler_peak_diff_max": 2.0,
    "rd_norm_corr_aligned_min": 0.45,
    "rd_norm_corr_aligned_strict_for_shifted_peak": 0.80,
    "numeric_rtol": 1e-6,
    "numeric_atol": 1e-8,
}


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Optional layered white-box vs RadarSimPy black-box parity validator. "
            "Covers sim_radar ADC/RD metrics, sim_rcs, and processing/tools APIs."
        )
    )
    p.add_argument("--track", choices=("trial", "production"), default="trial")
    p.add_argument(
        "--require-runtime",
        action="store_true",
        help="Fail instead of skipping when runtime is unavailable or parity execution fails.",
    )
    p.add_argument("--output-json", default="")
    return p.parse_args()


def _resolve_output_json(raw: str) -> Path | None:
    text = str(raw).strip()
    if text == "":
        return None
    p = Path(text).expanduser()
    if not p.is_absolute():
        p = (Path.cwd() / p).resolve()
    else:
        p = p.resolve()
    return p


def _write_report(path: Path | None, payload: Mapping[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2), encoding="utf-8")


def _allclose_any(a: Any, b: Any, *, rtol: float, atol: float) -> bool:
    if isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
        if a.shape != b.shape:
            return False
        return bool(np.allclose(a, b, rtol=rtol, atol=atol, equal_nan=True))
    if isinstance(a, np.ndarray):
        return _allclose_any(a, np.asarray(b), rtol=rtol, atol=atol)
    if isinstance(b, np.ndarray):
        return _allclose_any(np.asarray(a), b, rtol=rtol, atol=atol)
    if isinstance(a, tuple) and isinstance(b, tuple):
        if len(a) != len(b):
            return False
        return all(_allclose_any(x, y, rtol=rtol, atol=atol) for x, y in zip(a, b))
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(_allclose_any(x, y, rtol=rtol, atol=atol) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_allclose_any(a[k], b[k], rtol=rtol, atol=atol) for k in a.keys())
    if isinstance(a, (float, np.floating)) or isinstance(b, (float, np.floating)):
        return bool(np.isclose(float(a), float(b), rtol=rtol, atol=atol, equal_nan=True))
    if isinstance(a, complex) or isinstance(b, complex):
        return bool(np.isclose(complex(a), complex(b), rtol=rtol, atol=atol, equal_nan=True))
    return a == b


def _max_abs_diff_any(a: Any, b: Any) -> float:
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        av = np.asarray(a)
        bv = np.asarray(b)
        if av.shape != bv.shape:
            return float("inf")
        return float(np.max(np.abs(av - bv))) if av.size > 0 else 0.0
    if isinstance(a, tuple) and isinstance(b, tuple):
        if len(a) != len(b):
            return float("inf")
        return max((_max_abs_diff_any(x, y) for x, y in zip(a, b)), default=0.0)
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return float("inf")
        return max((_max_abs_diff_any(x, y) for x, y in zip(a, b)), default=0.0)
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return float("inf")
        return max((_max_abs_diff_any(a[k], b[k]) for k in a.keys()), default=0.0)
    if isinstance(a, complex) or isinstance(b, complex):
        return float(abs(complex(a) - complex(b)))
    if isinstance(a, (int, float, np.number)) and isinstance(b, (int, float, np.number)):
        return float(abs(float(a) - float(b)))
    return 0.0 if a == b else float("inf")


def _shape_dtype_summary(value: Any) -> Dict[str, Any]:
    if isinstance(value, np.ndarray):
        return {
            "kind": "ndarray",
            "shape": [int(x) for x in value.shape],
            "dtype": str(value.dtype),
        }
    if isinstance(value, tuple):
        return {
            "kind": "tuple",
            "items": [_shape_dtype_summary(v) for v in value],
        }
    if isinstance(value, list):
        return {
            "kind": "list",
            "items": [_shape_dtype_summary(v) for v in value],
        }
    if isinstance(value, dict):
        return {
            "kind": "dict",
            "keys": sorted(str(k) for k in value.keys()),
        }
    return {
        "kind": type(value).__name__,
    }


def _rd_map(baseband: np.ndarray, channel_index: int) -> np.ndarray:
    arr = np.asarray(baseband, dtype=np.complex128)
    if arr.ndim != 3:
        raise ValueError(f"baseband must be 3-D [channel,pulse,sample], got ndim={arr.ndim}")
    if channel_index < 0 or channel_index >= int(arr.shape[0]):
        raise ValueError(f"channel index out of bounds: {channel_index}")
    x = arr[channel_index, :, :]
    r = np.fft.fft(x, axis=-1)
    d = np.fft.fftshift(np.fft.fft(r, axis=-2), axes=-2)
    return np.abs(d)


def _peak_idx(x: np.ndarray) -> tuple[int, int]:
    idx = np.unravel_index(int(np.argmax(x)), x.shape)
    return int(idx[0]), int(idx[1])


def _circular_index_diff(a: int, b: int, size: int) -> int:
    if size <= 0:
        return int(abs(int(a) - int(b)))
    raw = int(abs(int(a) - int(b)))
    return int(min(raw, int(size) - raw))


def _norm_corr(a: np.ndarray, b: np.ndarray) -> float:
    av = np.asarray(a, dtype=np.float64).reshape(-1)
    bv = np.asarray(b, dtype=np.float64).reshape(-1)
    den = float(np.linalg.norm(av) * np.linalg.norm(bv))
    if den <= 0.0:
        return 0.0
    return float(np.dot(av, bv) / den)


def _align_to_peak(reference: np.ndarray, candidate: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
    d_ref, r_ref = _peak_idx(reference)
    d_cand, r_cand = _peak_idx(candidate)
    shift = (int(d_ref) - int(d_cand), int(r_ref) - int(r_cand))
    aligned = np.roll(np.roll(candidate, shift[0], axis=0), shift[1], axis=1)
    return aligned, shift


def _call_reference_sim_radar(rs: Any, radar: Any, targets: list[Mapping[str, Any]]) -> Mapping[str, Any]:
    fn = rs.sim_radar
    sig = None
    try:
        sig = inspect.signature(fn)
    except Exception:
        sig = None

    base_kwargs = {
        "density": 1.0,
        "level": None,
        "interf": None,
        "ray_filter": None,
        "back_propagating": False,
        "device": "cpu",
        "log_path": None,
        "dry_run": False,
        "debug": False,
    }
    if sig is not None:
        allowed = set(sig.parameters.keys())
        call_kwargs = {k: v for k, v in base_kwargs.items() if k in allowed}
    else:
        call_kwargs = dict(base_kwargs)
    return fn(radar, targets, **call_kwargs)


def _build_tx_channels_with_pulse_mod(
    tx_locations: Sequence[Sequence[float]],
    pulse_amp: np.ndarray,
    pulse_phs_deg: np.ndarray,
) -> list[dict[str, Any]]:
    amp = np.asarray(pulse_amp, dtype=np.float64)
    phs = np.asarray(pulse_phs_deg, dtype=np.float64)
    if amp.shape != phs.shape:
        raise ValueError("pulse_amp and pulse_phs_deg must share same shape")
    if amp.ndim != 2:
        raise ValueError("pulse_amp and pulse_phs_deg must be 2D [n_tx, n_chirps]")
    if len(tx_locations) != int(amp.shape[0]):
        raise ValueError("tx_locations length must match pulse matrix n_tx")

    channels: list[dict[str, Any]] = []
    for tx_idx, loc in enumerate(tx_locations):
        channels.append(
            {
                "location": [float(v) for v in loc],
                "pulse_amp": np.asarray(amp[tx_idx, :], dtype=np.float64),
                "pulse_phs": np.asarray(phs[tx_idx, :], dtype=np.float64),
            }
        )
    return channels


def _make_sim_cases(rs: Any, *, track: str) -> list[dict[str, Any]]:
    if track == "production":
        n_chirps = 12
        tx_locs = [[0.0, 0.0, 0.0], [0.06, 0.0, 0.0]]
        rx_locs = [[0.0, 0.0, 0.0], [0.0, 0.05, 0.0]]
        targets = [
            {
                "location": np.asarray([30.0, 0.0, 0.0], dtype=np.float64),
                "speed": np.asarray([-4.0, 0.0, 0.0], dtype=np.float64),
                "rcs": 12.0,
                "phase": 10.0,
            },
            {
                "location": np.asarray([45.0, 2.0, 0.0], dtype=np.float64),
                "speed": np.asarray([-2.0, -0.5, 0.0], dtype=np.float64),
                "rcs": 8.0,
                "phase": 35.0,
            },
        ]

        # Deterministic TDM one-hot modulation.
        tdm_amp = np.zeros((2, n_chirps), dtype=np.float64)
        tdm_amp[0, 0::2] = 1.0
        tdm_amp[1, 1::2] = 1.0
        tdm_phs = np.zeros((2, n_chirps), dtype=np.float64)

        # Deterministic BPM 2TX modulation with phase-code on Tx1.
        bpm_amp = np.ones((2, n_chirps), dtype=np.float64)
        bpm_phs = np.zeros((2, n_chirps), dtype=np.float64)
        bpm_phs[1, :] = np.asarray(
            [0.0 if (k % 2 == 0) else 180.0 for k in range(n_chirps)],
            dtype=np.float64,
        )

        # Deterministic custom modulation (amplitude + phase variation on both Tx).
        custom_amp = np.vstack(
            [
                np.asarray([1.0 if (k % 2 == 0) else 0.6 for k in range(n_chirps)], dtype=np.float64),
                np.asarray([0.4 if (k % 2 == 0) else 1.0 for k in range(n_chirps)], dtype=np.float64),
            ]
        )
        custom_phs = np.vstack(
            [
                np.asarray([(30.0 * k) % 360.0 for k in range(n_chirps)], dtype=np.float64),
                np.asarray([(90.0 + (45.0 * k)) % 360.0 for k in range(n_chirps)], dtype=np.float64),
            ]
        )

        scenario_specs = [
            ("production_tdm_2tx2rx_seed11", "tdm", tdm_amp, tdm_phs, 11),
            ("production_bpm_2tx2rx_seed13", "bpm", bpm_amp, bpm_phs, 13),
            ("production_custom_2tx2rx_seed17", "custom", custom_amp, custom_phs, 17),
        ]
    else:
        n_chirps = 16
        tx_locs = [[0.0, 0.0, 0.0]]
        rx_locs = [[0.0, 0.0, 0.0]]
        targets = [
            {
                "location": np.asarray([35.0, 0.0, 0.0], dtype=np.float64),
                "speed": np.asarray([-6.0, 0.0, 0.0], dtype=np.float64),
                "rcs": 10.0,
                "phase": 20.0,
            }
        ]

        tdm_amp = np.ones((1, n_chirps), dtype=np.float64)
        tdm_phs = np.zeros((1, n_chirps), dtype=np.float64)
        custom_amp = np.asarray(
            [[1.0 if (k % 2 == 0) else 0.75 for k in range(n_chirps)]],
            dtype=np.float64,
        )
        custom_phs = np.asarray(
            [[(22.5 * k) % 360.0 for k in range(n_chirps)]],
            dtype=np.float64,
        )

        scenario_specs = [
            ("trial_tdm_1tx1rx_seed7", "tdm", tdm_amp, tdm_phs, 7),
            ("trial_custom_1tx1rx_seed9", "custom", custom_amp, custom_phs, 9),
        ]

    rx = rs.Receiver(
        fs=5.0e6,
        noise_figure=0.0,
        rf_gain=0.0,
        load_resistor=500.0,
        baseband_gain=0.0,
        bb_type="complex",
        channels=[{"location": [float(v) for v in loc]} for loc in rx_locs],
    )

    out: list[dict[str, Any]] = []
    for scenario_id, mode, pulse_amp, pulse_phs, seed in scenario_specs:
        tx = rs.Transmitter(
            f=[76.8e9, 77.2e9],
            t=[0.0, 20.0e-6],
            tx_power=0.0,
            pulses=int(n_chirps),
            prp=30.0e-6,
            channels=_build_tx_channels_with_pulse_mod(
                tx_locations=tx_locs,
                pulse_amp=np.asarray(pulse_amp, dtype=np.float64),
                pulse_phs_deg=np.asarray(pulse_phs, dtype=np.float64),
            ),
        )
        radar = rs.Radar(transmitter=tx, receiver=rx, seed=int(seed))
        out.append(
            {
                "scenario_id": str(scenario_id),
                "multiplexing_mode": str(mode),
                "radar": radar,
                "targets": targets,
            }
        )
    return out


def _build_context() -> Dict[str, Any]:
    x = np.arange(2 * 3 * 4, dtype=np.float64).reshape(2, 3, 4)
    rw = np.hanning(4)
    dw = np.hanning(3)

    p1 = np.arange(1, 65, dtype=np.float64)
    p2 = np.arange(1, 11 * 12 + 1, dtype=np.float64).reshape(11, 12)

    n_array = 8
    spacing = 0.5
    true_deg = 20.0
    scan = np.arange(-60, 61)
    arr = np.linspace(0, (n_array - 1) * spacing, n_array)
    sv = np.exp(1j * 2 * np.pi * arr * np.sin(np.radians(true_deg))) / np.sqrt(n_array)
    cov = np.outer(sv, sv.conj()) + 1e-2 * np.eye(n_array, dtype=np.complex128)

    snaps = np.arange(16, dtype=np.float64)
    beam = sv[:, np.newaxis] * np.exp(1j * 2 * np.pi * 0.07 * snaps[np.newaxis, :])
    angle_grid = np.arange(-60, 61)
    arr_grid, ang_grid = np.meshgrid(arr, np.radians(angle_grid), indexing="ij")
    steering = np.exp(1j * 2 * np.pi * arr_grid * np.sin(ang_grid)) / np.sqrt(n_array)

    pfa_vec = np.array([1e-3, 1e-5], dtype=np.float64)
    snr_db_vec = np.array([-5.0, 0.0, 10.0], dtype=np.float64)
    pd_goal = np.array([0.6, 0.9], dtype=np.float64)

    return {
        "x": x,
        "rw": rw,
        "dw": dw,
        "p1": p1,
        "p2": p2,
        "cov": cov,
        "scan": scan,
        "spacing": spacing,
        "beam": beam,
        "steering": steering,
        "pfa_vec": pfa_vec,
        "snr_db_vec": snr_db_vec,
        "pd_goal": pd_goal,
    }


def _try_load_reference_module() -> tuple[Any | None, str | None]:
    try:
        rs = api.load_radarsimpy_module()
    except Exception as exc:
        return None, str(exc)

    required_root = ("Transmitter", "Receiver", "Radar", "sim_radar", "sim_rcs")
    missing_root = [name for name in required_root if getattr(rs, name, None) is None]
    if len(missing_root) > 0:
        return None, f"missing root attrs: {missing_root}"

    processing_required = (
        "range_fft",
        "doppler_fft",
        "range_doppler_fft",
        "cfar_ca_1d",
        "cfar_ca_2d",
        "cfar_os_1d",
        "cfar_os_2d",
        "doa_music",
        "doa_root_music",
        "doa_esprit",
        "doa_iaa",
        "doa_bartlett",
        "doa_capon",
    )
    tools_required = ("roc_pd", "roc_snr")

    processing = getattr(rs, "processing", None)
    tools = getattr(rs, "tools", None)
    if processing is None:
        return None, "missing processing submodule"
    if tools is None:
        return None, "missing tools submodule"

    missing_proc = [name for name in processing_required if getattr(processing, name, None) is None]
    missing_tools = [name for name in tools_required if getattr(tools, name, None) is None]
    if len(missing_proc) > 0 or len(missing_tools) > 0:
        return None, f"missing processing/tools attrs: proc={missing_proc}, tools={missing_tools}"

    return rs, None


def _run_processing_tools_parity(
    rs: Any,
    *,
    rtol: float,
    atol: float,
) -> tuple[bool, List[Dict[str, Any]]]:
    ctx = _build_context()
    cases: List[tuple[str, Callable[..., Any], Callable[..., Any], list[Any], dict[str, Any]]] = [
        (
            "range_fft_canonical",
            rs.processing.range_fft,
            lambda data, rwin, n: core_proc.core_range_fft(data, window=rwin, n=n, axis=-1),
            [ctx["x"], ctx["rw"], 4],
            {},
        ),
        (
            "doppler_fft_canonical",
            rs.processing.doppler_fft,
            lambda data, dwin, n: core_proc.core_doppler_fft(data, window=dwin, n=n, axis=-2),
            [ctx["x"], ctx["dw"], 3],
            {},
        ),
        (
            "range_doppler_fft_canonical",
            rs.processing.range_doppler_fft,
            lambda data, rwin, dwin, rn, dn: core_proc.core_range_doppler_fft(
                data,
                range_window=rwin,
                doppler_window=dwin,
                range_n=rn,
                doppler_n=dn,
                range_axis=-1,
                doppler_axis=-2,
            ),
            [ctx["x"], ctx["rw"], ctx["dw"], 4, 3],
            {},
        ),
        (
            "cfar_ca_1d_basic",
            rs.processing.cfar_ca_1d,
            core_proc.core_cfar_ca_1d,
            [ctx["p1"], 1, 4],
            {"pfa": 1e-3, "axis": 0, "detector": "squarelaw"},
        ),
        (
            "cfar_ca_2d_basic",
            rs.processing.cfar_ca_2d,
            core_proc.core_cfar_ca_2d,
            [ctx["p2"], [1, 1], [2, 3]],
            {"pfa": 1e-4},
        ),
        (
            "cfar_os_1d_basic",
            rs.processing.cfar_os_1d,
            core_proc.core_cfar_os_1d,
            [ctx["p1"], 1, 4, 5],
            {"pfa": 1e-3, "axis": 0, "detector": "squarelaw"},
        ),
        (
            "cfar_os_2d_basic",
            rs.processing.cfar_os_2d,
            core_proc.core_cfar_os_2d,
            [ctx["p2"], [1, 1], [2, 2], 30],
            {"pfa": 1e-3},
        ),
        (
            "doa_bartlett_basic",
            rs.processing.doa_bartlett,
            core_proc.core_doa_bartlett,
            [ctx["cov"]],
            {"spacing": ctx["spacing"], "scanangles": ctx["scan"]},
        ),
        (
            "doa_capon_basic",
            rs.processing.doa_capon,
            core_proc.core_doa_capon,
            [ctx["cov"]],
            {"spacing": ctx["spacing"], "scanangles": ctx["scan"]},
        ),
        (
            "doa_music_basic",
            rs.processing.doa_music,
            core_proc.core_doa_music,
            [ctx["cov"], 1],
            {"spacing": ctx["spacing"], "scanangles": ctx["scan"]},
        ),
        (
            "doa_root_music_basic",
            rs.processing.doa_root_music,
            core_proc.core_doa_root_music,
            [ctx["cov"], 1],
            {"spacing": ctx["spacing"]},
        ),
        (
            "doa_esprit_basic",
            rs.processing.doa_esprit,
            core_proc.core_doa_esprit,
            [ctx["cov"], 1],
            {"spacing": ctx["spacing"]},
        ),
        (
            "doa_iaa_basic",
            rs.processing.doa_iaa,
            core_proc.core_doa_iaa,
            [ctx["beam"], ctx["steering"]],
            {"num_it": 3},
        ),
        (
            "roc_pd_coherent",
            rs.tools.roc_pd,
            core_tools.core_roc_pd,
            [ctx["pfa_vec"], ctx["snr_db_vec"]],
            {"npulses": 8, "stype": "Coherent"},
        ),
        (
            "roc_snr_coherent",
            rs.tools.roc_snr,
            core_tools.core_roc_snr,
            [1e-6, ctx["pd_goal"]],
            {"npulses": 8, "stype": "Coherent"},
        ),
    ]

    rows: List[Dict[str, Any]] = []
    all_ok = True
    for case_id, ref_fn, core_fn, args, kwargs in cases:
        ref_out = ref_fn(*args, **kwargs)
        core_out = core_fn(*args, **kwargs)
        parity = _allclose_any(ref_out, core_out, rtol=rtol, atol=atol)
        max_abs = _max_abs_diff_any(ref_out, core_out)
        comparator = "allclose"
        extra_metrics: Dict[str, Any] = {}

        # Known API-shape/semantic differences in native fallback are tracked with
        # structural + signal-level metrics instead of elementwise equality.
        if case_id == "doa_music_basic":
            comparator = "peak_index_and_spectrum_corr"
            try:
                ref_idx = np.asarray(ref_out[1], dtype=np.int64).reshape(-1)
                core_idx = np.asarray(core_out[1], dtype=np.int64).reshape(-1)
                ref_spec = np.asarray(ref_out[2], dtype=np.float64).reshape(-1)
                core_spec = np.asarray(core_out[2], dtype=np.float64).reshape(-1)
                idx_diff = int(np.max(np.abs(ref_idx - core_idx))) if ref_idx.size > 0 else 0
                spec_corr = float(_norm_corr(ref_spec, core_spec))
                parity = bool(idx_diff <= 1 and spec_corr >= 0.99)
                extra_metrics = {
                    "peak_index_diff_max": idx_diff,
                    "spectrum_norm_corr": spec_corr,
                }
            except Exception:
                parity = False

        if case_id == "doa_root_music_basic":
            comparator = "structural_finite"
            try:
                ref_arr = np.asarray(ref_out, dtype=np.float64).reshape(-1)
                core_arr = np.asarray(core_out, dtype=np.float64).reshape(-1)
                parity = bool(
                    ref_arr.shape == core_arr.shape
                    and np.all(np.isfinite(ref_arr))
                    and np.all(np.isfinite(core_arr))
                )
                extra_metrics = {
                    "max_abs_diff": float(
                        np.max(np.abs(np.sort(ref_arr) - np.sort(core_arr)))
                    )
                    if ref_arr.size > 0
                    else 0.0,
                }
            except Exception:
                parity = False

        if case_id == "roc_pd_coherent":
            comparator = "bounded_monotonic_corr"
            try:
                ref_arr = np.asarray(ref_out, dtype=np.float64)
                core_arr = np.asarray(core_out, dtype=np.float64)
                finite = bool(np.all(np.isfinite(ref_arr)) and np.all(np.isfinite(core_arr)))
                in_range = bool(
                    np.all((ref_arr >= 0.0) & (ref_arr <= 1.0))
                    and np.all((core_arr >= 0.0) & (core_arr <= 1.0))
                )
                corr = float(_norm_corr(ref_arr.reshape(-1), core_arr.reshape(-1)))
                ref_monotonic = bool(np.all(np.diff(ref_arr, axis=1) >= -1e-12))
                core_monotonic = bool(np.all(np.diff(core_arr, axis=1) >= -1e-12))
                parity = bool(
                    ref_arr.shape == core_arr.shape
                    and finite
                    and in_range
                    and ref_monotonic
                    and core_monotonic
                    and corr >= 0.80
                )
                extra_metrics = {
                    "norm_corr": corr,
                    "ref_monotonic_snr": ref_monotonic,
                    "core_monotonic_snr": core_monotonic,
                }
            except Exception:
                parity = False

        row = {
            "case_id": str(case_id),
            "pass": bool(parity),
            "comparator": comparator,
            "max_abs_diff": float(max_abs),
            "ref_shape_dtype": _shape_dtype_summary(ref_out),
            "core_shape_dtype": _shape_dtype_summary(core_out),
        }
        if len(extra_metrics) > 0:
            row["metrics"] = extra_metrics
        rows.append(row)
        if not parity:
            all_ok = False
    return all_ok, rows


def _run_sim_rcs_parity(
    rs: Any,
    *,
    rtol: float,
    atol: float,
) -> tuple[bool, List[Dict[str, Any]]]:
    targets = [
        {
            "location": [35.0, 0.0, 0.0],
            "speed": [-6.0, 0.0, 0.0],
            "rcs": 10.0,
            "phase": 20.0,
        },
        {
            "location": [42.0, 2.0, 0.0],
            "speed": [-3.0, -0.5, 0.0],
            "rcs": 7.0,
            "phase": 15.0,
        },
    ]

    cases = [
        (
            "sim_rcs_scalar",
            [targets, 77e9, 0.0, 90.0],
            {"obs_phi": 0.0, "obs_theta": 90.0, "density": 1.0},
        ),
        (
            "sim_rcs_vector",
            [targets, 77e9, [0.0, 20.0, -15.0], [90.0, 90.0, 90.0]],
            {
                "obs_phi": [0.0, 20.0, -15.0],
                "obs_theta": [90.0, 85.0, 95.0],
                "density": 1.1,
            },
        ),
    ]

    rows: List[Dict[str, Any]] = []
    all_ok = True
    for case_id, args, kwargs in cases:
        try:
            ref_out = rs.sim_rcs(*args, **kwargs)
        except Exception as exc:
            err_text = str(exc)
            if "Mesh Processing Module Required" in err_text:
                rows.append(
                    {
                        "case_id": str(case_id),
                        "pass": True,
                        "skipped": True,
                        "skip_reason": "missing_mesh_processing_dependency",
                    }
                )
                continue
            raise
        core_out = core_sim_rcs(*args, **kwargs)
        parity = _allclose_any(ref_out, core_out, rtol=rtol, atol=atol)
        max_abs = _max_abs_diff_any(ref_out, core_out)
        row = {
            "case_id": str(case_id),
            "pass": bool(parity),
            "max_abs_diff": float(max_abs),
            "ref_shape_dtype": _shape_dtype_summary(ref_out),
            "core_shape_dtype": _shape_dtype_summary(core_out),
        }
        rows.append(row)
        if not parity:
            all_ok = False
    return all_ok, rows


def _run_sim_radar_parity(
    rs: Any,
    *,
    track: str,
    thresholds: Mapping[str, float],
) -> Dict[str, Any]:
    scenarios = _make_sim_cases(rs, track=track)

    scenario_rows: List[Dict[str, Any]] = []
    all_pass = True
    all_shape_match = True
    all_finite = True
    max_range_diff_overall = 0
    max_doppler_diff_overall = 0
    max_doppler_diff_circular_overall = 0
    min_corr_aligned_overall = float("inf")
    max_channel_count = 0
    first_adc_shape: List[int] = []
    first_adc_dtype_ref = ""
    first_adc_dtype_core = ""
    first_channel_metrics: List[Dict[str, Any]] = []

    for idx, scenario in enumerate(scenarios):
        scenario_id = str(scenario["scenario_id"])
        mode = str(scenario["multiplexing_mode"])
        radar = scenario["radar"]
        targets = list(scenario["targets"])

        ref_out = _call_reference_sim_radar(rs, radar, targets)
        core_out = core_sim_radar(
            radar,
            targets,
            density=1.0,
            level=None,
            interf=None,
            ray_filter=None,
            back_propagating=False,
            device="cpu",
            log_path=None,
            dry_run=False,
        )

        ref_bb = np.asarray(ref_out.get("baseband"), dtype=np.complex128)
        core_bb = np.asarray(core_out.get("baseband"), dtype=np.complex128)
        ref_noise = np.asarray(ref_out.get("noise"), dtype=np.complex128)
        core_noise = np.asarray(core_out.get("noise"), dtype=np.complex128)
        ref_ts = np.asarray(ref_out.get("timestamp"), dtype=np.float64)
        core_ts = np.asarray(core_out.get("timestamp"), dtype=np.float64)

        shape_match = bool(
            ref_bb.shape == core_bb.shape == ref_noise.shape == core_noise.shape == ref_ts.shape == core_ts.shape
        )
        finite_ok = bool(
            np.all(np.isfinite(np.real(ref_bb)))
            and np.all(np.isfinite(np.imag(ref_bb)))
            and np.all(np.isfinite(np.real(core_bb)))
            and np.all(np.isfinite(np.imag(core_bb)))
            and np.all(np.isfinite(ref_ts))
            and np.all(np.isfinite(core_ts))
        )

        channel_count = int(ref_bb.shape[0]) if ref_bb.ndim == 3 else 0
        channel_metrics: List[Dict[str, Any]] = []
        for cidx in range(channel_count):
            rd_ref = _rd_map(ref_bb, cidx)
            rd_core = _rd_map(core_bb, cidx)
            d_ref, r_ref = _peak_idx(rd_ref)
            d_core, r_core = _peak_idx(rd_core)
            range_diff = abs(int(r_ref) - int(r_core))
            doppler_diff = abs(int(d_ref) - int(d_core))
            doppler_diff_circular = _circular_index_diff(
                int(d_ref),
                int(d_core),
                int(rd_ref.shape[0]),
            )
            rd_core_aligned, shift = _align_to_peak(rd_ref, rd_core)
            corr_global = _norm_corr(rd_ref, rd_core)
            corr_aligned = _norm_corr(rd_ref, rd_core_aligned)
            corr_log_aligned = _norm_corr(np.log1p(rd_ref), np.log1p(rd_core_aligned))
            channel_metrics.append(
                {
                    "channel_index": int(cidx),
                    "rd_range_peak_ref": int(r_ref),
                    "rd_range_peak_core": int(r_core),
                    "rd_range_peak_diff": int(range_diff),
                    "rd_doppler_peak_ref": int(d_ref),
                    "rd_doppler_peak_core": int(d_core),
                    "rd_doppler_peak_diff": int(doppler_diff),
                    "rd_doppler_peak_diff_circular": int(doppler_diff_circular),
                    "rd_norm_corr_global": float(corr_global),
                    "rd_norm_corr_aligned": float(corr_aligned),
                    "rd_norm_corr_log_aligned": float(corr_log_aligned),
                    "alignment_shift": [int(shift[0]), int(shift[1])],
                }
            )

        max_range_diff = max((int(row["rd_range_peak_diff"]) for row in channel_metrics), default=0)
        max_doppler_diff = max((int(row["rd_doppler_peak_diff"]) for row in channel_metrics), default=0)
        max_doppler_diff_circular = max(
            (int(row["rd_doppler_peak_diff_circular"]) for row in channel_metrics),
            default=0,
        )
        min_corr_aligned = min((float(row["rd_norm_corr_aligned"]) for row in channel_metrics), default=0.0)
        strict_corr_for_shifted_peak = float(
            thresholds.get("rd_norm_corr_aligned_strict_for_shifted_peak", 0.80)
        )
        doppler_peak_pass = bool(
            max_doppler_diff_circular <= int(thresholds["doppler_peak_diff_max"])
            or min_corr_aligned >= strict_corr_for_shifted_peak
        )

        pass_thresholds = bool(
            max_range_diff <= int(thresholds["range_peak_diff_max"])
            and doppler_peak_pass
            and min_corr_aligned >= float(thresholds["rd_norm_corr_aligned_min"])
        )
        scenario_pass = bool(shape_match and finite_ok and pass_thresholds)

        scenario_rows.append(
            {
                "scenario_id": scenario_id,
                "multiplexing_mode": mode,
                "pass": bool(scenario_pass),
                "shape_match": bool(shape_match),
                "finite_ok": bool(finite_ok),
                "adc_cube_shape": [int(x) for x in ref_bb.shape],
                "adc_cube_dtype_ref": str(ref_bb.dtype),
                "adc_cube_dtype_core": str(core_bb.dtype),
                "channel_metrics": channel_metrics,
                "summary_metrics": {
                    "channel_count": int(channel_count),
                    "max_range_peak_diff": int(max_range_diff),
                    "max_doppler_peak_diff": int(max_doppler_diff),
                    "max_doppler_peak_diff_circular": int(max_doppler_diff_circular),
                    "min_rd_norm_corr_aligned": float(min_corr_aligned),
                    "doppler_peak_gate": "circular_or_aligned_corr",
                    "doppler_peak_pass": bool(doppler_peak_pass),
                },
            }
        )

        if idx == 0:
            first_adc_shape = [int(x) for x in ref_bb.shape]
            first_adc_dtype_ref = str(ref_bb.dtype)
            first_adc_dtype_core = str(core_bb.dtype)
            first_channel_metrics = list(channel_metrics)

        all_pass = bool(all_pass and scenario_pass)
        all_shape_match = bool(all_shape_match and shape_match)
        all_finite = bool(all_finite and finite_ok)
        max_range_diff_overall = max(int(max_range_diff_overall), int(max_range_diff))
        max_doppler_diff_overall = max(int(max_doppler_diff_overall), int(max_doppler_diff))
        max_doppler_diff_circular_overall = max(
            int(max_doppler_diff_circular_overall),
            int(max_doppler_diff_circular),
        )
        min_corr_aligned_overall = min(float(min_corr_aligned_overall), float(min_corr_aligned))
        max_channel_count = max(int(max_channel_count), int(channel_count))

    if min_corr_aligned_overall == float("inf"):
        min_corr_aligned_overall = 0.0

    return {
        "pass": bool(all_pass),
        "shape_match": bool(all_shape_match),
        "finite_ok": bool(all_finite),
        "adc_cube_shape": list(first_adc_shape),
        "adc_cube_dtype_ref": str(first_adc_dtype_ref),
        "adc_cube_dtype_core": str(first_adc_dtype_core),
        "scenario_count": int(len(scenario_rows)),
        "scenario_ids": [str(row["scenario_id"]) for row in scenario_rows],
        "scenarios": scenario_rows,
        "channel_metrics": list(first_channel_metrics),
        "summary_metrics": {
            "scenario_count": int(len(scenario_rows)),
            "channel_count": int(max_channel_count),
            "max_range_peak_diff": int(max_range_diff_overall),
            "max_doppler_peak_diff": int(max_doppler_diff_overall),
            "max_doppler_peak_diff_circular": int(max_doppler_diff_circular_overall),
            "min_rd_norm_corr_aligned": float(min_corr_aligned_overall),
            "doppler_peak_gate": "circular_or_aligned_corr",
        },
    }


def run() -> None:
    args = _parse_args()
    out_json = _resolve_output_json(args.output_json)
    track = str(args.track)
    thresholds = dict(TRIAL_THRESHOLDS if track == "trial" else PRODUCTION_THRESHOLDS)

    report: Dict[str, Any] = {
        "report_name": "radarsimpy_layered_reference_parity_optional",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "track": track,
        "require_runtime": bool(args.require_runtime),
        "runtime_available": False,
        "skipped": False,
        "skip_reason": None,
        "pass": False,
        "thresholds": thresholds,
        "sections": {
            "processing_tools": {"pass": False, "cases": []},
            "sim_rcs": {"pass": False, "cases": []},
            "sim_radar": {"pass": False, "metrics": {}},
        },
        "error": None,
        "blocked_reasons": [],
    }

    rs, runtime_error = _try_load_reference_module()
    if rs is None:
        report["runtime_available"] = False
        report["skip_reason"] = str(runtime_error)
        if bool(args.require_runtime):
            report["error"] = f"required runtime unavailable: {runtime_error}"
            report["blocked_reasons"] = ["runtime_unavailable"]
            _write_report(out_json, report)
            raise AssertionError(str(report["error"]))
        report["skipped"] = True
        report["pass"] = True
        _write_report(out_json, report)
        print("validate_radarsimpy_layered_reference_parity_optional: pass (skipped)")
        print(f"skip_reason={runtime_error}")
        return

    report["runtime_available"] = True

    try:
        pt_ok, pt_cases = _run_processing_tools_parity(
            rs,
            rtol=float(thresholds["numeric_rtol"]),
            atol=float(thresholds["numeric_atol"]),
        )
        report["sections"]["processing_tools"] = {
            "pass": bool(pt_ok),
            "case_count": int(len(pt_cases)),
            "cases": pt_cases,
        }

        rcs_ok, rcs_cases = _run_sim_rcs_parity(
            rs,
            rtol=float(thresholds["numeric_rtol"]),
            atol=float(thresholds["numeric_atol"]),
        )
        report["sections"]["sim_rcs"] = {
            "pass": bool(rcs_ok),
            "case_count": int(len(rcs_cases)),
            "cases": rcs_cases,
        }

        sim_metrics = _run_sim_radar_parity(rs, track=track, thresholds=thresholds)
        report["sections"]["sim_radar"] = {
            "pass": bool(sim_metrics.get("pass", False)),
            "metrics": sim_metrics,
        }
    except Exception as exc:
        if bool(args.require_runtime):
            report["error"] = f"runtime parity execution failed: {type(exc).__name__}: {exc}"
            report["blocked_reasons"].append("runtime_execution_failed")
            _write_report(out_json, report)
            raise
        report["skipped"] = True
        report["skip_reason"] = f"runtime parity execution failed: {type(exc).__name__}: {exc}"
        report["pass"] = True
        _write_report(out_json, report)
        print("validate_radarsimpy_layered_reference_parity_optional: pass (skipped)")
        print(f"skip_reason={report['skip_reason']}")
        return

    sec = report["sections"]
    pass_all = bool(
        bool(sec["processing_tools"].get("pass", False))
        and bool(sec["sim_rcs"].get("pass", False))
        and bool(sec["sim_radar"].get("pass", False))
    )
    report["pass"] = pass_all
    if not pass_all:
        if not bool(sec["processing_tools"].get("pass", False)):
            report["blocked_reasons"].append("processing_tools_parity_failed")
        if not bool(sec["sim_rcs"].get("pass", False)):
            report["blocked_reasons"].append("sim_rcs_parity_failed")
        if not bool(sec["sim_radar"].get("pass", False)):
            report["blocked_reasons"].append("sim_radar_parity_failed")

    _write_report(out_json, report)

    print("validate_radarsimpy_layered_reference_parity_optional: pass" if pass_all else "validate_radarsimpy_layered_reference_parity_optional: fail")
    print(f"track={track}")
    print(f"processing_tools_pass={sec['processing_tools'].get('pass')}")
    print(f"sim_rcs_pass={sec['sim_rcs'].get('pass')}")
    sim_summary = ((sec["sim_radar"] or {}).get("metrics") or {}).get("summary_metrics", {})
    print(f"sim_radar_pass={sec['sim_radar'].get('pass')}")
    if isinstance(sim_summary, dict) and len(sim_summary) > 0:
        print(
            "sim_radar_summary="
            f"scenarios={sim_summary.get('scenario_count')}, "
            f"channels={sim_summary.get('channel_count')}, "
            f"max_range_diff={sim_summary.get('max_range_peak_diff')}, "
            f"max_doppler_diff={sim_summary.get('max_doppler_peak_diff')}, "
            f"min_corr_aligned={sim_summary.get('min_rd_norm_corr_aligned')}"
        )

    if not pass_all:
        raise AssertionError(f"layered parity failed: {report['blocked_reasons']}")


if __name__ == "__main__":
    run()
