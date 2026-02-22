#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_po_sbr_executed_report_validator_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]

        out_dir = root / "outputs"
        out_dir.mkdir(parents=True, exist_ok=True)
        scene_json = out_dir / "scene_po_sbr_runtime_pilot.json"
        path_json = out_dir / "path_list.json"
        adc_npz = out_dir / "adc_cube.npz"
        radar_npz = out_dir / "radar_map.npz"
        for p in (scene_json, path_json, adc_npz, radar_npz):
            p.write_text("placeholder\n", encoding="utf-8")

        summary_json = root / "summary.json"
        summary = {
            "scene_id": "po_sbr_runtime_pilot_v1_linux",
            "pilot_status": "executed",
            "blockers": [],
            "diagnostics": {
                "platform": "Linux",
                "repo_exists": True,
                "geometry_exists": True,
                "missing_modules": [],
                "nvidia_runtime_available": True,
            },
            "recommended_linux_command": "PYTHONPATH=src python3 scripts/run_scene_runtime_po_sbr_pilot.py ...",
            "scene_json": str(scene_json.resolve()),
            "output_dir": str(out_dir.resolve()),
            "path_list_json": str(path_json.resolve()),
            "adc_cube_npz": str(adc_npz.resolve()),
            "radar_map_npz": str(radar_npz.resolve()),
            "frame_count": 8,
            "path_count": 8,
            "runtime_resolution": {
                "mode": "runtime_provider",
                "runtime_provider": "avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr",
            },
        }
        summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        proc = subprocess.run(
            [
                "python3",
                "scripts/validate_scene_runtime_po_sbr_executed_report.py",
                "--summary-json",
                str(summary_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "validate_scene_runtime_po_sbr_executed_report: pass" in proc.stdout, proc.stdout

    print("validate_validate_scene_runtime_po_sbr_executed_report: pass")


if __name__ == "__main__":
    run()
