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


def _assert_contract(payload: Mapping[str, Any]) -> None:
    assert payload.get("report_name") == "radarsimpy_layered_parity_suite"
    assert isinstance(payload.get("generated_at_utc"), str)
    assert isinstance(payload.get("track_count"), int)
    assert isinstance(payload.get("pass_count"), int)
    assert isinstance(payload.get("fail_count"), int)
    assert isinstance(payload.get("required_fail_count"), int)
    assert isinstance(payload.get("pass"), bool)
    tracks = payload.get("tracks")
    assert isinstance(tracks, list)
    for row in tracks:
        assert isinstance(row, dict)
        assert isinstance(row.get("name"), str)
        assert isinstance(row.get("required"), bool)
        run = row.get("run")
        assert isinstance(run, dict)
        assert isinstance(run.get("returncode"), int)
        assert isinstance(run.get("pass"), bool)


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "run_radarsimpy_layered_parity_suite.py"
    py = str((repo_root / ".venv" / "bin" / "python") if (repo_root / ".venv" / "bin" / "python").exists() else Path(sys.executable))

    with tempfile.TemporaryDirectory(prefix="validate_run_radarsimpy_layered_parity_suite_") as td:
        root = Path(td)

        out1 = root / "suite_default.json"
        env1 = dict(os.environ)
        env1["PYTHONPATH"] = str(repo_root / "src")
        p1 = _run(
            [
                py,
                str(script),
                "--output-json",
                str(out1),
            ],
            cwd=repo_root,
            env=env1,
        )
        if p1.returncode != 0:
            raise AssertionError(
                "layered parity suite failed in default mode\n"
                f"stdout:\n{p1.stdout}\n"
                f"stderr:\n{p1.stderr}\n"
            )
        payload1 = _load_json(out1)
        _assert_contract(payload1)
        assert payload1.get("track_count") == 1
        assert payload1.get("pass") is True

        trial_pkg_root = (
            repo_root / "external" / "radarsimpy_trial" / "Ubuntu24_x86_64_CPU" / "Ubuntu24_x86_64_CPU"
        ).resolve()
        libcompat_dir = (
            repo_root / "external" / "radarsimpy_trial" / "libcompat" / "usr" / "lib" / "x86_64-linux-gnu"
        ).resolve()

        if trial_pkg_root.exists() and libcompat_dir.exists():
            out2 = root / "suite_trial_runtime.json"
            env2 = dict(os.environ)
            env2["PYTHONPATH"] = str(repo_root / "src")
            p2 = _run(
                [
                    py,
                    str(script),
                    "--output-json",
                    str(out2),
                    "--require-runtime-trial",
                    "--trial-package-root",
                    str(trial_pkg_root),
                    "--libcompat-dir",
                    str(libcompat_dir),
                ],
                cwd=repo_root,
                env=env2,
            )
            if p2.returncode != 0:
                raise AssertionError(
                    "layered parity suite failed in trial runtime mode\n"
                    f"stdout:\n{p2.stdout}\n"
                    f"stderr:\n{p2.stderr}\n"
                )
            payload2 = _load_json(out2)
            _assert_contract(payload2)
            assert payload2.get("track_count") == 1
            assert payload2.get("pass") is True

    print("validate_run_radarsimpy_layered_parity_suite: pass")


if __name__ == "__main__":
    run()
