#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from avxsim.adapters import to_radarsimpy_view


def _save_adc_npz(path: Path, adc_sctr: np.ndarray) -> None:
    np.savez_compressed(
        str(path),
        adc=np.asarray(adc_sctr, dtype=np.complex64),
        metadata_json=json.dumps({"shape_sctr": [int(x) for x in adc_sctr.shape]}),
    )


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_radarsimpy_periodic_lock_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        n_s, n_c, n_t, n_r = 32, 4, 2, 2
        t = np.arange(n_s, dtype=np.float64) / float(n_s)
        base_tone = np.exp(1j * 2.0 * np.pi * (3.0 * t))
        adc = np.zeros((n_s, n_c, n_t, n_r), dtype=np.complex64)
        for c in range(n_c):
            for tx in range(n_t):
                for rx in range(n_r):
                    phase = np.exp(1j * 2.0 * np.pi * 0.1 * (c + tx + rx))
                    adc[:, c, tx, rx] = (phase * base_tone).astype(np.complex64)

        pass_adc_npz = root / "adc_pass.npz"
        fail_adc_npz = root / "adc_fail.npz"
        _save_adc_npz(pass_adc_npz, adc)
        _save_adc_npz(fail_adc_npz, adc * 1.5)

        reference_view = to_radarsimpy_view(adc)
        ref_view_npz = root / "reference_view.npz"
        np.savez_compressed(str(ref_view_npz), view=np.asarray(reference_view, dtype=np.complex64))

        manifest_pass_json = root / "manifest_pass.json"
        manifest_pass_json.write_text(
            json.dumps(
                {
                    "cases": [
                        {
                            "case_id": "pass_case",
                            "candidate_adc_npz": str(pass_adc_npz),
                            "candidate_adc_key": "adc",
                            "candidate_adc_order": "sctr",
                            "reference_view_npz": str(ref_view_npz),
                            "reference_view_key": "view",
                        }
                    ]
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        summary_pass_json = root / "summary_pass.json"
        proc_pass = subprocess.run(
            [
                "python3",
                "scripts/run_radarsimpy_periodic_parity_lock.py",
                "--manifest-json",
                str(manifest_pass_json),
                "--output-summary-json",
                str(summary_pass_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "RadarSimPy periodic parity lock completed." in proc_pass.stdout, proc_pass.stdout
        summary_pass = json.loads(summary_pass_json.read_text(encoding="utf-8"))
        assert summary_pass["pass"] is True
        assert summary_pass["pass_count"] == 1
        assert summary_pass["fail_count"] == 0

        manifest_mixed_json = root / "manifest_mixed.json"
        manifest_mixed_json.write_text(
            json.dumps(
                {
                    "cases": [
                        {
                            "case_id": "pass_case",
                            "candidate_adc_npz": str(pass_adc_npz),
                            "reference_view_npz": str(ref_view_npz),
                        },
                        {
                            "case_id": "fail_case",
                            "candidate_adc_npz": str(fail_adc_npz),
                            "reference_view_npz": str(ref_view_npz),
                        },
                    ]
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        thresholds_json = root / "strict_thresholds.json"
        thresholds_json.write_text(
            json.dumps(
                {
                    "view_nmse_max": 1e-10,
                    "power_nmse_max": 1e-10,
                    "mean_abs_error_max": 1e-8,
                    "max_abs_error_max": 1e-6,
                    "complex_corr_abs_min": 0.999999,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        summary_mixed_json = root / "summary_mixed.json"
        proc_mixed = subprocess.run(
            [
                "python3",
                "scripts/run_radarsimpy_periodic_parity_lock.py",
                "--manifest-json",
                str(manifest_mixed_json),
                "--thresholds-json",
                str(thresholds_json),
                "--output-summary-json",
                str(summary_mixed_json),
                "--allow-failures",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "RadarSimPy periodic parity lock completed." in proc_mixed.stdout, proc_mixed.stdout
        summary_mixed = json.loads(summary_mixed_json.read_text(encoding="utf-8"))
        assert summary_mixed["pass"] is False
        assert summary_mixed["pass_count"] == 1
        assert summary_mixed["fail_count"] == 1
        assert summary_mixed["runtime_info"]["radarsimpy"]["available"] is False

    print("validate_run_radarsimpy_periodic_parity_lock: pass")


if __name__ == "__main__":
    run()
