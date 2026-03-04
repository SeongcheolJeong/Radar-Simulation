#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import inspect
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np

import avxsim.radarsimpy_api as api
from avxsim.radarsimpy_core_simulator import core_sim_radar


def _rd_map(baseband: np.ndarray) -> np.ndarray:
    arr = np.asarray(baseband, dtype=np.complex128)
    if arr.ndim != 3:
        raise ValueError(f"baseband must be 3-D [channel,pulse,sample], got ndim={arr.ndim}")
    # Use first channel for robust point-target parity metrics.
    x = arr[0, :, :]
    r = np.fft.fft(x, axis=-1)
    d = np.fft.fftshift(np.fft.fft(r, axis=-2), axes=-2)
    return np.abs(d)


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


def _peak_idx(x: np.ndarray) -> tuple[int, int]:
    idx = np.unravel_index(int(np.argmax(x)), x.shape)
    return int(idx[0]), int(idx[1])


def _try_load_reference_module() -> tuple[Any | None, str | None]:
    try:
        rs = api.load_radarsimpy_module()
    except Exception as exc:  # pragma: no cover - env dependent
        return None, str(exc)

    required = ("Transmitter", "Receiver", "Radar", "sim_radar")
    missing = [name for name in required if getattr(rs, name, None) is None]
    if len(missing) > 0:
        return None, f"missing attrs: {missing}"
    return rs, None


def _print_skip(reason: str) -> None:
    print("validate_radarsimpy_simulator_reference_parity_optional: pass (skipped)")
    print(f"skip_reason={reason}")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Optional RadarSimPy simulator parity validator. "
            "Skips when runtime is unavailable unless --require-runtime is set."
        )
    )
    p.add_argument(
        "--require-runtime",
        action="store_true",
        help="Fail instead of skipping when RadarSimPy runtime is unavailable or execution fails.",
    )
    p.add_argument(
        "--output-json",
        default="",
        help="Optional JSON output path for parity report.",
    )
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


def _make_reference_case(rs: Any) -> tuple[Any, list[Mapping[str, Any]]]:
    # Trial-safe 1x1 geometry + point target.
    tx = rs.Transmitter(
        f=[76.8e9, 77.2e9],
        t=[0.0, 20.0e-6],
        tx_power=0.0,
        pulses=16,
        prp=30.0e-6,
        channels=[{"location": [0.0, 0.0, 0.0]}],
    )
    rx = rs.Receiver(
        fs=5.0e6,
        noise_figure=0.0,
        rf_gain=0.0,
        load_resistor=500.0,
        baseband_gain=0.0,
        bb_type="complex",
        channels=[{"location": [0.0, 0.0, 0.0]}],
    )
    radar = rs.Radar(transmitter=tx, receiver=rx, seed=7)
    targets = [
        {
            "location": np.asarray([35.0, 0.0, 0.0], dtype=np.float64),
            "speed": np.asarray([-6.0, 0.0, 0.0], dtype=np.float64),
            "rcs": 10.0,
            "phase": 20.0,
        }
    ]
    return radar, targets


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


def run() -> None:
    args = _parse_args()
    out_json = _resolve_output_json(args.output_json)
    report: dict[str, Any] = {
        "report_name": "radarsimpy_simulator_reference_parity_optional",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "require_runtime": bool(args.require_runtime),
        "runtime_available": False,
        "skipped": False,
        "skip_reason": None,
        "pass": False,
        "metrics": {},
        "thresholds": {
            "range_peak_diff_max": 2,
            "doppler_peak_diff_max": 2,
            "rd_norm_corr_aligned_min": 0.60,
        },
        "error": None,
    }
    rs, skip_reason = _try_load_reference_module()
    if rs is None:
        report["runtime_available"] = False
        report["skip_reason"] = str(skip_reason)
        if bool(args.require_runtime):
            report["pass"] = False
            report["error"] = f"required runtime unavailable: {skip_reason}"
            _write_report(out_json, report)
            raise AssertionError(f"required runtime unavailable: {skip_reason}")
        report["skipped"] = True
        report["pass"] = True
        _write_report(out_json, report)
        _print_skip(str(skip_reason))
        return

    radar, targets = _make_reference_case(rs)
    try:
        ref_out = _call_reference_sim_radar(rs, radar, targets)
    except Exception as exc:  # pragma: no cover - env dependent
        report["runtime_available"] = True
        report["skip_reason"] = f"reference sim_radar execution failed: {type(exc).__name__}: {exc}"
        if bool(args.require_runtime):
            report["pass"] = False
            report["error"] = (
                f"required runtime execution failed: {type(exc).__name__}: {exc}"
            )
            _write_report(out_json, report)
            raise AssertionError(
                f"required runtime execution failed: {type(exc).__name__}: {exc}"
            ) from exc
        report["skipped"] = True
        report["pass"] = True
        _write_report(out_json, report)
        _print_skip(f"reference sim_radar execution failed: {type(exc).__name__}: {exc}")
        return

    fb_out = core_sim_radar(
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
    fb_bb = np.asarray(fb_out.get("baseband"), dtype=np.complex128)

    assert ref_bb.shape == fb_bb.shape, (ref_bb.shape, fb_bb.shape)
    assert ref_bb.ndim == 3, ref_bb.shape
    assert np.all(np.isfinite(np.real(ref_bb))) and np.all(np.isfinite(np.imag(ref_bb)))
    assert np.all(np.isfinite(np.real(fb_bb))) and np.all(np.isfinite(np.imag(fb_bb)))

    rd_ref = _rd_map(ref_bb)
    rd_fb = _rd_map(fb_bb)

    d_ref, r_ref = _peak_idx(rd_ref)
    d_fb, r_fb = _peak_idx(rd_fb)
    doppler_diff = abs(int(d_ref) - int(d_fb))
    range_diff = abs(int(r_ref) - int(r_fb))
    rd_fb_aligned, shift = _align_to_peak(rd_ref, rd_fb)
    corr_global = _norm_corr(rd_ref, rd_fb)
    corr_aligned = _norm_corr(rd_ref, rd_fb_aligned)
    corr_log_aligned = _norm_corr(np.log1p(rd_ref), np.log1p(rd_fb_aligned))

    report["runtime_available"] = True
    report["metrics"] = {
        "rd_range_peak_ref": int(r_ref),
        "rd_range_peak_fallback": int(r_fb),
        "rd_range_peak_diff": int(range_diff),
        "rd_doppler_peak_ref": int(d_ref),
        "rd_doppler_peak_fallback": int(d_fb),
        "rd_doppler_peak_diff": int(doppler_diff),
        "rd_norm_corr_global": float(corr_global),
        "rd_norm_corr_aligned": float(corr_aligned),
        "rd_norm_corr_log_aligned": float(corr_log_aligned),
        "alignment_shift": [int(shift[0]), int(shift[1])],
    }

    pass_range = bool(range_diff <= 2)
    pass_doppler = bool(doppler_diff <= 2)
    pass_corr = bool(math.isfinite(corr_aligned) and (corr_aligned >= 0.60))
    report["pass"] = bool(pass_range and pass_doppler and pass_corr)
    _write_report(out_json, report)
    if not bool(report["pass"]):
        raise AssertionError(
            {
                "range_check": pass_range,
                "doppler_check": pass_doppler,
                "corr_check": pass_corr,
                "metrics": report["metrics"],
                "thresholds": report["thresholds"],
            }
        )

    print("validate_radarsimpy_simulator_reference_parity_optional: pass")
    print(f"rd_range_peak_ref={r_ref}, rd_range_peak_fallback={r_fb}, diff={range_diff}")
    print(f"rd_doppler_peak_ref={d_ref}, rd_doppler_peak_fallback={d_fb}, diff={doppler_diff}")
    print(f"rd_norm_corr_global={corr_global:.6f}")
    print(f"rd_norm_corr_aligned={corr_aligned:.6f}")
    print(f"rd_norm_corr_log_aligned={corr_log_aligned:.6f}")
    print(f"alignment_shift={shift}")


if __name__ == "__main__":
    run()
