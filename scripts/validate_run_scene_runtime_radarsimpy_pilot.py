#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_scene_runtime_radarsimpy_pilot_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        out_root = root / "pilot_outputs"
        out_json = root / "pilot_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/run_scene_runtime_radarsimpy_pilot.py",
                "--output-root",
                str(out_root),
                "--output-summary-json",
                str(out_json),
                "--n-chirps",
                "6",
                "--samples-per-chirp",
                "512",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Scene runtime RadarSimPy pilot completed." in proc.stdout, proc.stdout
        summary = json.loads(out_json.read_text(encoding="utf-8"))
        assert summary.get("pilot_status") == "executed"
        assert isinstance(summary.get("blockers"), list)
        diagnostics = summary.get("diagnostics")
        assert isinstance(diagnostics, dict)
        assert summary.get("recommended_command")
        assert int(summary["frame_count"]) == 6
        assert int(summary["path_count"]) > 0
        runtime_resolution = summary.get("runtime_resolution")
        assert isinstance(runtime_resolution, dict)
        mode = str(runtime_resolution.get("mode", ""))
        assert mode in ("runtime_provider", "runtime_failed_fallback_static")
        if mode == "runtime_provider":
            assert str(runtime_resolution.get("runtime_provider", "")).endswith(
                "generate_radarsimpy_like_paths"
            )
            assert bool(summary.get("runtime_fallback_used", False)) is False
        else:
            assert bool(summary.get("runtime_fallback_used", False)) is True
            assert "runtime_error" in runtime_resolution

    print("validate_run_scene_runtime_radarsimpy_pilot: pass")


if __name__ == "__main__":
    run()
