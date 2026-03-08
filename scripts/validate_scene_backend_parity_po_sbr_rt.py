#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_po_sbr_parity_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        py = str((repo_root / ".venv" / "bin" / "python") if (repo_root / ".venv" / "bin" / "python").exists() else Path(sys.executable))

        out_root = root / "parity_run"
        out_json = root / "scene_backend_parity_po_sbr_rt.json"

        proc = subprocess.run(
            [
                py,
                "scripts/run_scene_backend_parity_po_sbr_rt.py",
                "--output-root",
                str(out_root),
                "--output-json",
                str(out_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "run_scene_backend_parity_po_sbr_rt: done" in proc.stdout, proc.stdout

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["report_name"] == "scene_backend_parity_po_sbr_rt"
        assert payload["reference_backend_type"] == "analytic_targets"
        assert payload["candidate_backend_type"] == "po_sbr_rt"
        assert payload["pass"] is True
        assert payload["parity"]["pass"] is True
        assert Path(payload["reference_radar_map_npz"]).exists()
        assert Path(payload["candidate_radar_map_npz"]).exists()

    print("validate_scene_backend_parity_po_sbr_rt: pass")


if __name__ == "__main__":
    run()
