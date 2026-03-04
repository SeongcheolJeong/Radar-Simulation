#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping


def _run(cmd: list[str], *, cwd: Path, env: Mapping[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=dict(env),
        capture_output=True,
        text=True,
        check=False,
    )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"expected object json at {path}")
    return payload


def _assert_common_report_contract(payload: Mapping[str, Any]) -> None:
    assert payload.get("report_name") == "radarsimpy_simulator_reference_parity_optional"
    assert isinstance(payload.get("generated_at_utc"), str)
    assert isinstance(payload.get("require_runtime"), bool)
    assert isinstance(payload.get("runtime_available"), bool)
    assert isinstance(payload.get("skipped"), bool)
    assert ("metrics" in payload) and isinstance(payload.get("metrics"), dict)
    thr = payload.get("thresholds")
    assert isinstance(thr, dict)
    assert "range_peak_diff_max" in thr
    assert "doppler_peak_diff_max" in thr
    assert "rd_norm_corr_aligned_min" in thr
    assert isinstance(payload.get("pass"), bool)


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "validate_radarsimpy_simulator_reference_parity_optional.py"
    py_path = repo_root / ".venv" / "bin" / "python"
    py = str(py_path if py_path.exists() else Path(sys.executable))

    with tempfile.TemporaryDirectory(prefix="validate_run_radarsimpy_sim_ref_parity_") as td:
        root = Path(td)

        # Case 1: default env (runtime may be unavailable) must still emit report + pass.
        out1 = root / "optional_case.json"
        env1 = dict(os.environ)
        env1["PYTHONPATH"] = str(repo_root / "src")
        p1 = _run([py, str(script), "--output-json", str(out1)], cwd=repo_root, env=env1)
        if p1.returncode != 0:
            raise AssertionError(
                "optional parity script failed in default mode\n"
                f"stdout:\n{p1.stdout}\n"
                f"stderr:\n{p1.stderr}\n"
            )
        payload1 = _load_json(out1)
        _assert_common_report_contract(payload1)
        assert bool(payload1.get("pass")) is True
        if bool(payload1.get("skipped")):
            assert isinstance(payload1.get("skip_reason"), str)
            assert payload1.get("runtime_available") is False
        else:
            m = payload1.get("metrics", {})
            assert "rd_norm_corr_aligned" in m

        # Case 2: strict runtime mode when trial package exists.
        trial_pkg_root = (
            repo_root / "external" / "radarsimpy_trial" / "Ubuntu24_x86_64_CPU" / "Ubuntu24_x86_64_CPU"
        ).resolve()
        libcompat_dir = (
            repo_root / "external" / "radarsimpy_trial" / "libcompat" / "usr" / "lib" / "x86_64-linux-gnu"
        ).resolve()
        if trial_pkg_root.exists() and libcompat_dir.exists():
            out2 = root / "real_runtime_case.json"
            env2 = dict(os.environ)
            env2["PYTHONPATH"] = f"{repo_root / 'src'}{os.pathsep}{trial_pkg_root}"
            env2["LD_LIBRARY_PATH"] = f"{libcompat_dir}{os.pathsep}{env2.get('LD_LIBRARY_PATH', '')}"
            p2 = _run(
                [
                    py,
                    str(script),
                    "--require-runtime",
                    "--output-json",
                    str(out2),
                ],
                cwd=repo_root,
                env=env2,
            )
            if p2.returncode != 0:
                raise AssertionError(
                    "optional parity script failed in strict runtime mode\n"
                    f"stdout:\n{p2.stdout}\n"
                    f"stderr:\n{p2.stderr}\n"
                )
            payload2 = _load_json(out2)
            _assert_common_report_contract(payload2)
            assert payload2.get("require_runtime") is True
            assert payload2.get("runtime_available") is True
            assert payload2.get("skipped") is False
            assert payload2.get("pass") is True
            metrics2 = payload2.get("metrics", {})
            assert int(metrics2.get("rd_range_peak_diff", 999)) <= int(
                payload2["thresholds"]["range_peak_diff_max"]
            )
            assert int(metrics2.get("rd_doppler_peak_diff", 999)) <= int(
                payload2["thresholds"]["doppler_peak_diff_max"]
            )
            assert float(metrics2.get("rd_norm_corr_aligned", -1.0)) >= float(
                payload2["thresholds"]["rd_norm_corr_aligned_min"]
            )

    print("validate_run_radarsimpy_simulator_reference_parity_optional: pass")


if __name__ == "__main__":
    run()
