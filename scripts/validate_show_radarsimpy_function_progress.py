#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "show_radarsimpy_function_progress.py"

    with tempfile.TemporaryDirectory(prefix="validate_show_radarsimpy_function_progress_") as td:
        root = Path(td)
        out_json = root / "function_progress.json"

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
            capture_output=True,
            text=True,
            check=True,
        )
        assert "RadarSimPy function progress" in proc.stdout, proc.stdout

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload.get("report_name") == "radarsimpy_function_progress"
        assert payload.get("ready") is True
        assert payload.get("all_supported_implemented") is True
        assert payload.get("all_supported_exported") is True
        assert payload.get("excluded_policy_ok") is True

        supported_count = int(payload.get("supported_count", -1))
        implemented_supported_count = int(payload.get("implemented_supported_count", -1))
        assert supported_count == 20, supported_count
        assert implemented_supported_count == supported_count
        assert payload.get("missing_supported") == []
        assert payload.get("unexported_supported") == []
        assert payload.get("excluded_violations") == []

        excluded_entries = payload.get("excluded_entries")
        assert isinstance(excluded_entries, list)
        assert len(excluded_entries) == 1
        row = dict(excluded_entries[0])
        assert row.get("symbol") == "sim_lidar"
        assert row.get("implemented") is False
        assert row.get("exported") is False

    print("validate_show_radarsimpy_function_progress: pass")


if __name__ == "__main__":
    run()
