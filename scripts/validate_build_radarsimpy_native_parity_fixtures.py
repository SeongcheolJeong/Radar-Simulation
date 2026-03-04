#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

import numpy as np

import avxsim.radarsimpy_api as api


def _build_sim_fixture_case_inputs(
    fixture_id: str,
):
    from avxsim.radarsimpy_core_model import CoreRadar, CoreReceiver, CoreTransmitter

    tx = CoreTransmitter(
        f=[76.8e9, 77.2e9],
        t=[0.0, 20.0e-6],
        tx_power=0.0,
        pulses=16,
        prp=30.0e-6,
        channels=[{"location": [0.0, 0.0, 0.0]}],
    )
    rx = CoreReceiver(
        fs=5.0e6,
        noise_figure=0.0,
        rf_gain=0.0,
        load_resistor=500.0,
        baseband_gain=0.0,
        bb_type="complex",
        channels=[{"location": [0.0, 0.0, 0.0]}],
    )
    radar = CoreRadar(transmitter=tx, receiver=rx, seed=7)
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


def _deserialize_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_deserialize_value(v) for v in value]
    if isinstance(value, dict):
        t = value.get("__type__")
        if t == "ndarray":
            shape = tuple(int(x) for x in list(value.get("shape", [])))
            real = np.asarray(list(value.get("real", [])), dtype=np.float64).reshape(shape)
            if "imag" in value:
                imag = np.asarray(list(value.get("imag", [])), dtype=np.float64).reshape(shape)
                out = real + 1j * imag
            else:
                out = real
            dtype_name = str(value.get("dtype", "float64"))
            return out.astype(np.dtype(dtype_name), copy=False)
        if t == "complex":
            return complex(float(value.get("re", 0.0)), float(value.get("im", 0.0)))
        if t == "range":
            return range(
                int(value.get("start", 0)),
                int(value.get("stop", 0)),
                int(value.get("step", 1)),
            )
        if t == "tuple":
            return tuple(_deserialize_value(v) for v in list(value.get("items", [])))
        return {str(k): _deserialize_value(v) for k, v in value.items()}
    return value


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
        return {"__type__": "range", "start": int(value.start), "stop": int(value.stop), "step": int(value.step)}
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


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_radarsimpy_native_parity_fixtures.py"

    env = dict(os.environ)
    env["PYTHONPATH"] = f"src{os.pathsep}{env['PYTHONPATH']}" if "PYTHONPATH" in env else "src"

    with tempfile.TemporaryDirectory(prefix="validate_radarsimpy_native_parity_fixtures_") as td:
        out_json = Path(td) / "fixtures.json"
        proc = subprocess.run(
            [
                str(Path(sys.executable)),
                str(script_path),
                "--repo-root",
                str(repo_root),
                "--output-json",
                str(out_json),
                "--strict-ready",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "RadarSimPy native parity fixtures" in proc.stdout, proc.stdout

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload.get("report_name") == "radarsimpy_native_parity_fixtures"
        assert payload.get("ready") is True
        assert int(payload.get("case_count", -1)) >= 20
        assert int(payload.get("native_api_count", -1)) == 17

        cases = payload.get("cases")
        assert isinstance(cases, list)
        assert len(cases) == int(payload.get("case_count", -2))

        old_resolve = api._resolve_submodule_attr
        old_resolve_root = api._resolve_root_attr
        forced_processing = set(api.RADARSIMPY_PROCESSING_API)
        forced_tools = set(api.RADARSIMPY_TOOLS_API)
        forced_root = {"sim_radar", "sim_rcs"}

        def _resolve_with_forced_missing(submodule_name: str, attr_name: str):
            if submodule_name == "processing" and attr_name in forced_processing:
                raise RuntimeError(f"forced missing processing attr: {attr_name}")
            if submodule_name == "tools" and attr_name in forced_tools:
                raise RuntimeError(f"forced missing tools attr: {attr_name}")
            return old_resolve(submodule_name, attr_name)

        def _resolve_root_with_forced_missing(name: str):
            if name in forced_root:
                raise RuntimeError(f"forced missing root attr: {name}")
            return old_resolve_root(name)

        try:
            api._resolve_submodule_attr = _resolve_with_forced_missing
            api._resolve_root_attr = _resolve_root_with_forced_missing

            for row in cases:
                case = dict(row)
                api_symbol = str(case.get("api_symbol"))
                fn = getattr(api, api_symbol, None)
                assert callable(fn), api_symbol

                fixture_id_raw = case.get("fixture_id")
                if isinstance(fixture_id_raw, str) and fixture_id_raw.strip() != "":
                    args, kwargs = _build_sim_fixture_case_inputs(str(fixture_id_raw).strip())
                else:
                    args = _deserialize_value(case.get("args"))
                    kwargs = _deserialize_value(case.get("kwargs"))
                    assert isinstance(args, list), type(args)
                    assert isinstance(kwargs, dict), type(kwargs)

                got = fn(*args, **kwargs)
                expected = _deserialize_value(case.get("expected_native"))

                assert _allclose_any(got, expected), f"parity mismatch: {case.get('case_id')}"

                got_ser = _serialize_value(got)
                got_digest = _json_digest(got_ser)
                exp_digest = str(case.get("expected_native_digest"))
                assert got_digest == exp_digest, f"digest mismatch: {case.get('case_id')}"
        finally:
            api._resolve_submodule_attr = old_resolve
            api._resolve_root_attr = old_resolve_root

    print("validate_build_radarsimpy_native_parity_fixtures: pass")


if __name__ == "__main__":
    run()
