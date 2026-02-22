#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _assert_mitsuba_available() -> None:
    try:
        import mitsuba  # type: ignore  # noqa: F401
    except Exception as exc:
        raise RuntimeError(
            "mitsuba is required for this validation. "
            "Use the dedicated runtime venv (e.g., .venv-sionna311)."
        ) from exc


def run() -> None:
    _assert_mitsuba_available()
    with tempfile.TemporaryDirectory(prefix="validate_scene_runtime_mitsuba_pilot_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        out_root = root / "pilot_outputs"
        out_json = root / "pilot_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/run_scene_runtime_mitsuba_pilot.py",
                "--output-root",
                str(out_root),
                "--output-summary-json",
                str(out_json),
                "--n-chirps",
                "6",
                "--samples-per-chirp",
                "512",
                "--target-range-m",
                "24.0",
                "--target-radius-m",
                "0.6",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Scene runtime Mitsuba pilot completed." in proc.stdout, proc.stdout

        summary = json.loads(out_json.read_text(encoding="utf-8"))
        assert int(summary["frame_count"]) == 6
        assert int(summary["path_count"]) > 0
        runtime_resolution = summary["runtime_resolution"]
        assert isinstance(runtime_resolution, dict)
        assert runtime_resolution["mode"] == "runtime_provider"
        assert str(runtime_resolution.get("runtime_provider", "")).endswith(
            "generate_sionna_like_paths_from_mitsuba"
        )

    print("validate_run_scene_runtime_mitsuba_pilot: pass")


if __name__ == "__main__":
    run()
