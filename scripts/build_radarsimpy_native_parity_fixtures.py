#!/usr/bin/env python3
"""Build deterministic golden parity fixtures for native RadarSimPy fallbacks."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import numpy as np


PROCESSING_APIS: Tuple[str, ...] = (
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
TOOLS_APIS: Tuple[str, ...] = ("roc_pd", "roc_snr")
SIMULATOR_APIS: Tuple[str, ...] = ("sim_radar", "sim_rcs")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Build deterministic golden parity fixtures for RadarSimPy native "
            "processing/tools/simulator fallbacks."
        )
    )
    p.add_argument("--repo-root", default=".")
    p.add_argument("--output-json", required=True)
    p.add_argument(
        "--include-reference",
        action="store_true",
        help="Also run optional parity checks against installed radarsimpy runtime.",
    )
    p.add_argument("--strict-ready", action="store_true")
    return p.parse_args()


def _load_module(repo_root: Path, module_name: str) -> ModuleType:
    src_root = (repo_root / "src").resolve()
    if not src_root.exists():
        raise FileNotFoundError(f"missing src root: {src_root}")
    src_text = str(src_root)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)
    return importlib.import_module(module_name)


def _serialize_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        arr = value
        out: Dict[str, Any] = {
            "__type__": "ndarray",
            "dtype": str(arr.dtype),
            "shape": [int(x) for x in arr.shape],
            "real": np.asarray(np.real(arr), dtype=np.float64).reshape(-1).tolist(),
        }
        if np.iscomplexobj(arr):
            out["imag"] = np.asarray(np.imag(arr), dtype=np.float64).reshape(-1).tolist()
        return out
    if isinstance(value, np.generic):
        return _serialize_value(value.item())
    if isinstance(value, complex):
        return {"__type__": "complex", "re": float(value.real), "im": float(value.imag)}
    if isinstance(value, range):
        return {
            "__type__": "range",
            "start": int(value.start),
            "stop": int(value.stop),
            "step": int(value.step),
        }
    if isinstance(value, tuple):
        return {"__type__": "tuple", "items": [_serialize_value(v) for v in value]}
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    if value is None:
        return None
    if isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError(f"unsupported type for serialization: {type(value)!r}")


def _json_digest(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _allclose_any(a: Any, b: Any, *, rtol: float = 1e-9, atol: float = 1e-12) -> bool:
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


def _reference_callable(rs: ModuleType, api_symbol: str) -> Any:
    if api_symbol in PROCESSING_APIS:
        sub = getattr(rs, "processing", None)
        if sub is None:
            return None
        return getattr(sub, api_symbol, None)
    if api_symbol in TOOLS_APIS:
        sub = getattr(rs, "tools", None)
        if sub is None:
            return None
        return getattr(sub, api_symbol, None)
    # Simulator/root parity is tracked in dedicated runtime validators.
    return None


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


def _build_sim_fixture_case_inputs(
    fixture_id: str,
    *,
    core_model: ModuleType,
) -> tuple[list[Any], dict[str, Any]]:
    tx = core_model.CoreTransmitter(
        f=[76.8e9, 77.2e9],
        t=[0.0, 20.0e-6],
        tx_power=0.0,
        pulses=16,
        prp=30.0e-6,
        channels=[{"location": [0.0, 0.0, 0.0]}],
    )
    rx = core_model.CoreReceiver(
        fs=5.0e6,
        noise_figure=0.0,
        rf_gain=0.0,
        load_resistor=500.0,
        baseband_gain=0.0,
        bb_type="complex",
        channels=[{"location": [0.0, 0.0, 0.0]}],
    )
    radar = core_model.CoreRadar(transmitter=tx, receiver=rx, seed=7)
    targets = [
        {
            "location": [35.0, 0.0, 0.0],
            "speed": [-6.0, 0.0, 0.0],
            "rcs": 10.0,
            "phase": 20.0,
        }
    ]

    if fixture_id == "sim_radar_basic":
        return (
            [radar, targets],
            {
                "density": 1.0,
                "level": None,
                "interf": None,
                "ray_filter": None,
                "back_propagating": False,
                "device": "cpu",
                "log_path": None,
                "dry_run": False,
            },
        )
    if fixture_id == "sim_radar_dry_run":
        return (
            [radar, targets],
            {
                "density": 1.0,
                "level": None,
                "interf": None,
                "ray_filter": None,
                "back_propagating": False,
                "device": "cpu",
                "log_path": None,
                "dry_run": True,
            },
        )
    if fixture_id == "sim_rcs_scalar":
        return (
            [targets, 77e9, 0.0, 90.0],
            {
                "obs_phi": 0.0,
                "obs_theta": 90.0,
                "density": 1.0,
            },
        )
    if fixture_id == "sim_rcs_vector":
        return (
            [targets, 77e9, [0.0, 20.0, -15.0], [90.0, 90.0, 90.0]],
            {
                "obs_phi": [0.0, 20.0, -15.0],
                "obs_theta": [90.0, 85.0, 95.0],
                "density": 1.1,
            },
        )
    raise ValueError(f"unknown fixture_id: {fixture_id}")


def main() -> None:
    args = parse_args()
    repo_root = Path(str(args.repo_root)).expanduser().resolve()
    output_json = Path(str(args.output_json)).expanduser()
    if not output_json.is_absolute():
        output_json = (repo_root / output_json).resolve()
    else:
        output_json = output_json.resolve()

    wrapper_api = _load_module(repo_root, "avxsim.radarsimpy_api")
    core_proc = _load_module(repo_root, "avxsim.radarsimpy_core_processing")
    core_tools = _load_module(repo_root, "avxsim.radarsimpy_core_tools")
    core_model = _load_module(repo_root, "avxsim.radarsimpy_core_model")
    core_simulator = _load_module(repo_root, "avxsim.radarsimpy_core_simulator")

    ctx = _build_context()

    cases_spec: List[Dict[str, Any]] = [
        {
            "case_id": "range_fft_canonical",
            "api": "range_fft",
            "args": [ctx["x"], ctx["rw"], 4],
            "kwargs": {},
            "expected": core_proc.core_range_fft(ctx["x"], window=ctx["rw"], n=4, axis=-1),
        },
        {
            "case_id": "doppler_fft_canonical",
            "api": "doppler_fft",
            "args": [ctx["x"], ctx["dw"], 3],
            "kwargs": {},
            "expected": core_proc.core_doppler_fft(ctx["x"], window=ctx["dw"], n=3, axis=-2),
        },
        {
            "case_id": "range_doppler_fft_canonical",
            "api": "range_doppler_fft",
            "args": [ctx["x"], ctx["rw"], ctx["dw"], 4, 3],
            "kwargs": {},
            "expected": core_proc.core_range_doppler_fft(
                ctx["x"],
                range_window=ctx["rw"],
                doppler_window=ctx["dw"],
                range_n=4,
                doppler_n=3,
                range_axis=-1,
                doppler_axis=-2,
            ),
        },
        {
            "case_id": "cfar_ca_1d_basic",
            "api": "cfar_ca_1d",
            "args": [ctx["p1"], 1, 4],
            "kwargs": {"pfa": 1e-3, "axis": 0, "detector": "squarelaw"},
            "expected": core_proc.core_cfar_ca_1d(
                ctx["p1"], 1, 4, pfa=1e-3, axis=0, detector="squarelaw"
            ),
        },
        {
            "case_id": "cfar_ca_2d_basic",
            "api": "cfar_ca_2d",
            "args": [ctx["p2"], [1, 1], [2, 3]],
            "kwargs": {"pfa": 1e-4},
            "expected": core_proc.core_cfar_ca_2d(ctx["p2"], [1, 1], [2, 3], pfa=1e-4),
        },
        {
            "case_id": "cfar_os_1d_basic",
            "api": "cfar_os_1d",
            "args": [ctx["p1"], 1, 4, 5],
            "kwargs": {"pfa": 1e-3, "axis": 0, "detector": "squarelaw"},
            "expected": core_proc.core_cfar_os_1d(
                ctx["p1"], 1, 4, 5, pfa=1e-3, axis=0, detector="squarelaw"
            ),
        },
        {
            "case_id": "cfar_os_2d_basic",
            "api": "cfar_os_2d",
            "args": [ctx["p2"], [1, 1], [2, 2], 30],
            "kwargs": {"pfa": 1e-3},
            "expected": core_proc.core_cfar_os_2d(ctx["p2"], [1, 1], [2, 2], 30, pfa=1e-3),
        },
        {
            "case_id": "doa_bartlett_basic",
            "api": "doa_bartlett",
            "args": [ctx["cov"]],
            "kwargs": {"spacing": ctx["spacing"], "scanangles": ctx["scan"]},
            "expected": core_proc.core_doa_bartlett(
                ctx["cov"], spacing=ctx["spacing"], scanangles=ctx["scan"]
            ),
        },
        {
            "case_id": "doa_capon_basic",
            "api": "doa_capon",
            "args": [ctx["cov"]],
            "kwargs": {"spacing": ctx["spacing"], "scanangles": ctx["scan"]},
            "expected": core_proc.core_doa_capon(
                ctx["cov"], spacing=ctx["spacing"], scanangles=ctx["scan"]
            ),
        },
        {
            "case_id": "doa_music_basic",
            "api": "doa_music",
            "args": [ctx["cov"], 1],
            "kwargs": {"spacing": ctx["spacing"], "scanangles": ctx["scan"]},
            "expected": core_proc.core_doa_music(
                ctx["cov"], 1, spacing=ctx["spacing"], scanangles=ctx["scan"]
            ),
        },
        {
            "case_id": "doa_root_music_basic",
            "api": "doa_root_music",
            "args": [ctx["cov"], 1],
            "kwargs": {"spacing": ctx["spacing"]},
            "expected": core_proc.core_doa_root_music(ctx["cov"], 1, spacing=ctx["spacing"]),
        },
        {
            "case_id": "doa_esprit_basic",
            "api": "doa_esprit",
            "args": [ctx["cov"], 1],
            "kwargs": {"spacing": ctx["spacing"]},
            "expected": core_proc.core_doa_esprit(ctx["cov"], 1, spacing=ctx["spacing"]),
        },
        {
            "case_id": "doa_iaa_basic",
            "api": "doa_iaa",
            "args": [ctx["beam"], ctx["steering"]],
            "kwargs": {"num_it": 3},
            "expected": core_proc.core_doa_iaa(ctx["beam"], ctx["steering"], num_it=3),
        },
        {
            "case_id": "roc_pd_coherent",
            "api": "roc_pd",
            "args": [ctx["pfa_vec"], ctx["snr_db_vec"]],
            "kwargs": {"npulses": 8, "stype": "Coherent"},
            "expected": core_tools.core_roc_pd(
                ctx["pfa_vec"], ctx["snr_db_vec"], npulses=8, stype="Coherent"
            ),
        },
        {
            "case_id": "roc_pd_swerling1",
            "api": "roc_pd",
            "args": [ctx["pfa_vec"], ctx["snr_db_vec"]],
            "kwargs": {"npulses": 8, "stype": "Swerling 1"},
            "expected": core_tools.core_roc_pd(
                ctx["pfa_vec"], ctx["snr_db_vec"], npulses=8, stype="Swerling 1"
            ),
        },
        {
            "case_id": "roc_snr_coherent",
            "api": "roc_snr",
            "args": [1e-6, ctx["pd_goal"]],
            "kwargs": {"npulses": 8, "stype": "Coherent"},
            "expected": core_tools.core_roc_snr(1e-6, ctx["pd_goal"], npulses=8, stype="Coherent"),
        },
        {
            "case_id": "sim_radar_basic",
            "api": "sim_radar",
            "fixture_id": "sim_radar_basic",
        },
        {
            "case_id": "sim_radar_dry_run",
            "api": "sim_radar",
            "fixture_id": "sim_radar_dry_run",
        },
        {
            "case_id": "sim_rcs_scalar",
            "api": "sim_rcs",
            "fixture_id": "sim_rcs_scalar",
        },
        {
            "case_id": "sim_rcs_vector",
            "api": "sim_rcs",
            "fixture_id": "sim_rcs_vector",
        },
    ]

    reference_module: ModuleType | None = None
    reference_error: str | None = None
    if bool(args.include_reference):
        try:
            loader = getattr(wrapper_api, "load_radarsimpy_module", None)
            if not callable(loader):
                raise RuntimeError("wrapper missing load_radarsimpy_module")
            reference_module = loader()
        except Exception as exc:  # pragma: no cover - env dependent
            reference_module = None
            reference_error = str(exc)

    cases_out: List[Dict[str, Any]] = []
    reference_compared_count = 0
    reference_pass_count = 0
    reference_fail_count = 0
    reference_error_count = 0

    for spec in cases_spec:
        fixture_id = spec.get("fixture_id")
        args_runtime: list[Any]
        kwargs_runtime: dict[str, Any]
        if fixture_id is None:
            args_runtime = list(spec["args"])
            kwargs_runtime = dict(spec["kwargs"])
            expected_value = spec["expected"]
        else:
            args_runtime, kwargs_runtime = _build_sim_fixture_case_inputs(
                str(fixture_id),
                core_model=core_model,
            )
            api_symbol = str(spec["api"])
            if api_symbol == "sim_radar":
                expected_value = core_simulator.core_sim_radar(*args_runtime, **kwargs_runtime)
            elif api_symbol == "sim_rcs":
                expected_value = core_simulator.core_sim_rcs(*args_runtime, **kwargs_runtime)
            else:
                raise ValueError(f"unexpected simulator api symbol: {api_symbol}")

        expected_serialized = _serialize_value(expected_value)
        row: Dict[str, Any] = {
            "case_id": str(spec["case_id"]),
            "api_symbol": str(spec["api"]),
            "fixture_id": None if fixture_id is None else str(fixture_id),
            "args": _serialize_value(spec["args"]) if fixture_id is None else None,
            "kwargs": _serialize_value(spec["kwargs"]) if fixture_id is None else None,
            "expected_native": expected_serialized,
            "expected_native_digest": _json_digest(expected_serialized),
        }

        ref_payload: Dict[str, Any] = {"available": False, "status": "missing"}
        if reference_module is not None:
            ref_callable = _reference_callable(reference_module, str(spec["api"]))
            if callable(ref_callable):
                reference_compared_count += 1
                try:
                    ref_out = ref_callable(*args_runtime, **kwargs_runtime)
                    ref_ok = _allclose_any(ref_out, expected_value)
                    ref_serialized = _serialize_value(ref_out)
                    ref_payload = {
                        "available": True,
                        "status": "pass" if ref_ok else "fail",
                        "output_digest": _json_digest(ref_serialized),
                    }
                    if ref_ok:
                        reference_pass_count += 1
                    else:
                        reference_fail_count += 1
                except Exception as exc:  # pragma: no cover - env dependent
                    reference_error_count += 1
                    ref_payload = {
                        "available": True,
                        "status": "error",
                        "error": str(exc),
                    }
            else:
                ref_payload = {"available": False, "status": "missing_callable"}
        row["reference"] = ref_payload
        cases_out.append(row)

    reference_ready = bool(reference_compared_count > 0 and reference_fail_count == 0 and reference_error_count == 0)

    report = {
        "report_name": "radarsimpy_native_parity_fixtures",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(repo_root),
        "fixture_version": 1,
        "case_count": int(len(cases_out)),
        "case_ids": [str(row["case_id"]) for row in cases_out],
        "native_api_count": int(len(set(str(row["api_symbol"]) for row in cases_out))),
        "reference_runtime_available": bool(reference_module is not None),
        "reference_runtime_import_error": reference_error,
        "reference_parity": {
            "compared_count": int(reference_compared_count),
            "pass_count": int(reference_pass_count),
            "fail_count": int(reference_fail_count),
            "error_count": int(reference_error_count),
            "ready": reference_ready,
        },
        "ready": bool(
            len(cases_out) > 0
            and (
                (reference_module is None)
                or reference_ready
            )
        ),
        "cases": cases_out,
    }

    print("RadarSimPy native parity fixtures")
    print(f"workspace_root={report['workspace_root']}")
    print(f"case_count={report['case_count']}")
    print(f"native_api_count={report['native_api_count']}")
    print(f"reference_runtime_available={report['reference_runtime_available']}")
    print(f"reference_parity_ready={report['reference_parity']['ready']}")
    print(f"ready={report['ready']}")

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {output_json}")

    if bool(args.strict_ready) and not bool(report["ready"]):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
