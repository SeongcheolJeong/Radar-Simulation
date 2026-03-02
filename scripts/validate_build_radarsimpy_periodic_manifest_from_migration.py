#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np


def _write_adc_npz(path: Path, adc_sctr: np.ndarray) -> None:
    np.savez_compressed(
        str(path),
        adc=np.asarray(adc_sctr, dtype=np.complex64),
        metadata_json=json.dumps({"shape_sctr": [int(x) for x in adc_sctr.shape]}),
    )


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_build_periodic_manifest_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        n_s, n_c, n_t, n_r = 16, 4, 1, 1
        t = np.arange(n_s, dtype=np.float64) / float(n_s)
        base = np.exp(1j * 2.0 * np.pi * (2.0 * t))
        adc_ref = np.zeros((n_s, n_c, n_t, n_r), dtype=np.complex64)
        for c in range(n_c):
            adc_ref[:, c, 0, 0] = (np.exp(1j * 0.1 * c) * base).astype(np.complex64)
        adc_ok = np.asarray(adc_ref, dtype=np.complex64)
        adc_scaled = np.asarray(adc_ref * 1.25, dtype=np.complex64)

        ref_adc_npz = root / "ref_adc.npz"
        ok_adc_npz = root / "ok_adc.npz"
        scaled_adc_npz = root / "scaled_adc.npz"
        _write_adc_npz(ref_adc_npz, adc_ref)
        _write_adc_npz(ok_adc_npz, adc_ok)
        _write_adc_npz(scaled_adc_npz, adc_scaled)

        migration_summary_json = root / "migration_summary.json"
        migration_summary_json.write_text(
            json.dumps(
                {
                    "reference_backend": "radarsimpy_rt",
                    "migration_status": "ready",
                    "reference": {
                        "status": "executed",
                        "adc_cube_npz": str(ref_adc_npz),
                    },
                    "steps": [
                        {
                            "backend": "analytic_targets",
                            "status": "compared",
                            "parity_pass": True,
                            "adc_cube_npz": str(ok_adc_npz),
                        },
                        {
                            "backend": "sionna_rt",
                            "status": "compared",
                            "parity_pass": False,
                            "adc_cube_npz": str(scaled_adc_npz),
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        manifest_json = root / "manifest.json"
        reference_view_npz = root / "reference_view.npz"

        proc = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/build_radarsimpy_periodic_manifest_from_migration.py",
                "--migration-summary-json",
                str(migration_summary_json),
                "--output-manifest-json",
                str(manifest_json),
                "--output-reference-view-npz",
                str(reference_view_npz),
                "--require-compared",
                "--require-parity-pass",
                "--strict",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "RadarSimPy periodic manifest build completed." in proc.stdout, proc.stdout

        manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
        assert int(manifest.get("case_count", -1)) == 1
        assert int(manifest.get("skipped_count", -1)) >= 1
        assert len(manifest.get("cases", [])) == 1
        row = manifest["cases"][0]
        assert row["backend"] == "analytic_targets"
        assert row["candidate_adc_npz"] == str(ok_adc_npz.resolve())
        assert row["reference_view_npz"] == str(reference_view_npz.resolve())
        assert row["candidate_adc_order"] == "sctr"
        assert row["reference_view_key"] == "view"

        with np.load(str(reference_view_npz), allow_pickle=False) as payload:
            assert "view" in payload
            assert payload["view"].ndim == 3
            assert payload["view"].shape[1] == n_c

        periodic_summary_json = root / "periodic_summary.json"
        proc2 = subprocess.run(
            [
                str(Path(sys.executable)),
                "scripts/run_radarsimpy_periodic_parity_lock.py",
                "--manifest-json",
                str(manifest_json),
                "--output-summary-json",
                str(periodic_summary_json),
                "--normalization-mode",
                "complex_l2",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "RadarSimPy periodic parity lock completed." in proc2.stdout, proc2.stdout
        periodic = json.loads(periodic_summary_json.read_text(encoding="utf-8"))
        assert periodic["pass"] is True
        assert periodic["case_count"] == 1
        assert periodic["pass_count"] == 1
        assert periodic["fail_count"] == 0
        assert periodic["normalization_mode"] == "complex_l2"

    print("validate_build_radarsimpy_periodic_manifest_from_migration: pass")


if __name__ == "__main__":
    run()
