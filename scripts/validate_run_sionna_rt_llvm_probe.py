#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_sionna_rt_llvm_probe_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        out_json = root / "llvm_probe_summary.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        proc = subprocess.run(
            [
                "python3",
                "scripts/run_sionna_rt_llvm_probe.py",
                "--output-summary-json",
                str(out_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Sionna RT LLVM probe completed." in proc.stdout, proc.stdout

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert isinstance(payload.get("python_executable"), str)
        assert isinstance(payload.get("candidate_count"), int)
        assert isinstance(payload.get("probe_count"), int)
        assert isinstance(payload.get("success"), bool)
        assert payload["probe_count"] >= 1
        results = payload.get("results")
        assert isinstance(results, list) and len(results) >= 1
        for item in results:
            assert "candidate_path" in item
            assert isinstance(item.get("success"), bool)
            assert isinstance(item.get("return_code"), int)
            assert isinstance(item.get("stdout"), str)
            assert isinstance(item.get("stderr"), str)

        if payload["success"]:
            assert payload.get("working_libllvm_path") is not None

    print("validate_run_sionna_rt_llvm_probe: pass")


if __name__ == "__main__":
    run()
