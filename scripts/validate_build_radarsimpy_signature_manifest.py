#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "build_radarsimpy_signature_manifest.py"

    env = dict(os.environ)
    env["PYTHONPATH"] = f"src{os.pathsep}{env['PYTHONPATH']}" if "PYTHONPATH" in env else "src"

    with tempfile.TemporaryDirectory(prefix="validate_radarsimpy_signature_manifest_") as td:
        out_json = Path(td) / "manifest.json"
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
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "RadarSimPy signature manifest" in proc.stdout, proc.stdout

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload.get("report_name") == "radarsimpy_signature_manifest"
        assert payload.get("ready") is True
        assert payload.get("phase1_native_ready") is True
        assert int(payload.get("total_count", -1)) == 20
        assert int(payload.get("canonical_defined_count", -1)) == 20
        assert int(payload.get("native_core_count", -1)) == 15
        assert int(payload.get("exported_count", -1)) == 20

        rows = payload.get("entries")
        assert isinstance(rows, list)
        assert len(rows) == 20

        by_qual = {str(row.get("qualified_symbol")): dict(row) for row in rows}

        root_rows = [row for row in rows if str(row.get("category")) == "root"]
        proc_rows = [row for row in rows if str(row.get("category")) == "processing"]
        tool_rows = [row for row in rows if str(row.get("category")) == "tools"]
        assert len(root_rows) == 5
        assert len(proc_rows) == 13
        assert len(tool_rows) == 2

        for row in root_rows:
            assert row.get("has_native_core") is False
            assert isinstance(row.get("canonical_signature"), str)
            assert isinstance(row.get("wrapper_signature"), str)

        for row in [*proc_rows, *tool_rows]:
            assert row.get("has_native_core") is True
            assert isinstance(row.get("native_core_symbol"), str)
            assert isinstance(row.get("native_core_signature"), str)
            assert isinstance(row.get("canonical_signature"), str)

        assert by_qual["radarsimpy.processing.range_fft"]["canonical_signature"] == "(data, rwin=None, n=None)"
        assert by_qual["radarsimpy.processing.doppler_fft"]["canonical_signature"] == "(data, dwin=None, n=None)"
        assert by_qual["radarsimpy.processing.range_doppler_fft"]["canonical_signature"] == (
            "(data, rwin=None, dwin=None, rn=None, dn=None)"
        )
        assert by_qual["radarsimpy.tools.roc_pd"]["canonical_signature"] == (
            "(pfa, snr, npulses=1, stype='Coherent')"
        )
        assert by_qual["radarsimpy.tools.roc_snr"]["canonical_signature"] == (
            "(pfa, pd, npulses=1, stype='Coherent')"
        )

    print("validate_build_radarsimpy_signature_manifest: pass")


if __name__ == "__main__":
    run()
