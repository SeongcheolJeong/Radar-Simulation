#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_scene_runtime_po_sbr_pilot_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        out_root = root / "pilot_outputs"
        out_json = root / "pilot_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/run_scene_runtime_po_sbr_pilot.py",
                "--output-root",
                str(out_root),
                "--output-summary-json",
                str(out_json),
                "--n-chirps",
                "6",
                "--samples-per-chirp",
                "512",
                "--allow-blocked",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Scene runtime PO-SBR pilot completed." in proc.stdout, proc.stdout
        summary = json.loads(out_json.read_text(encoding="utf-8"))
        assert summary.get("pilot_status") in ("blocked", "executed")
        assert isinstance(summary.get("blockers"), list)
        diagnostics = summary.get("diagnostics")
        assert isinstance(diagnostics, dict)
        assert summary.get("recommended_linux_command")

        if summary["pilot_status"] == "executed":
            assert int(summary["frame_count"]) == 6
            assert int(summary["path_count"]) > 0
            runtime_resolution = summary.get("runtime_resolution")
            assert isinstance(runtime_resolution, dict)
            assert runtime_resolution.get("mode") == "runtime_provider"
            assert str(runtime_resolution.get("runtime_provider", "")).endswith(
                "generate_po_sbr_like_paths_from_posbr"
            )
        else:
            blockers = list(summary["blockers"])
            assert len(blockers) > 0
            assert any(
                (b == "missing_required_modules")
                or (b == "missing_nvidia_runtime")
                or str(b).startswith("unsupported_platform:")
                for b in blockers
            )

    print("validate_run_scene_runtime_po_sbr_pilot: pass")


if __name__ == "__main__":
    run()
