#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_scene_runtime_probe_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        out_json = root / "runtime_probe_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        proc = subprocess.run(
            [
                "python3",
                "scripts/run_scene_runtime_env_probe.py",
                "--workspace-root",
                str(repo_root),
                "--output-summary-json",
                str(out_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Scene runtime environment probe completed." in proc.stdout, proc.stdout

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert isinstance(payload.get("python"), dict)
        assert isinstance(payload.get("module_report"), dict)
        runtime_report = payload.get("runtime_report")
        assert isinstance(runtime_report, dict)
        assert "sionna_runtime" in runtime_report
        assert "po_sbr_runtime" in runtime_report

        for runtime_name in ("sionna_runtime", "po_sbr_runtime"):
            info = runtime_report[runtime_name]
            assert isinstance(info, dict)
            assert isinstance(info.get("required_modules"), list)
            assert isinstance(info.get("missing_required_modules"), list)
            assert isinstance(info.get("repo_candidates"), list)
            assert isinstance(info.get("found_repo_paths"), list)
            assert isinstance(info.get("missing_repo_paths"), list)
            expected_ready = bool(info.get("repo_found")) and len(info["missing_required_modules"]) == 0
            assert bool(info["ready"]) is expected_ready

    print("validate_run_scene_runtime_env_probe: pass")


if __name__ == "__main__":
    run()
