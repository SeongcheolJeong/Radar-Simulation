#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from avxsim.calibration import (
    apply_global_jones_matrix,
    fit_global_jones_matrix,
    load_global_jones_matrix_json,
)


def run() -> None:
    rng = np.random.default_rng(42)
    n = 256

    tx = rng.normal(size=(n, 2)) + 1j * rng.normal(size=(n, 2))
    rx = rng.normal(size=(n, 2)) + 1j * rng.normal(size=(n, 2))
    path = rng.normal(size=(n, 2, 2)) + 1j * rng.normal(size=(n, 2, 2))
    for i in range(n):
        path[i, :, :] += np.eye(2)

    j_true = np.asarray(
        [
            [1.1 + 0.2j, -0.15 + 0.05j],
            [0.08 - 0.02j, 0.9 - 0.1j],
        ],
        dtype=np.complex128,
    )
    y = apply_global_jones_matrix(
        tx_jones=tx,
        rx_jones=rx,
        global_jones_matrix=j_true,
        path_matrices=path,
    )
    noise = (rng.normal(size=n) + 1j * rng.normal(size=n)) * 1e-4
    y_noisy = y + noise

    fit = fit_global_jones_matrix(
        tx_jones=tx,
        rx_jones=rx,
        observed_gain=y_noisy,
        path_matrices=path,
        ridge=1e-6,
    )
    j_hat = np.asarray(fit["global_jones_matrix"], dtype=np.complex128)
    rel = np.linalg.norm(j_hat - j_true) / (np.linalg.norm(j_true) + 1e-12)
    assert rel < 2e-3, rel
    assert fit["metrics"]["nmse"] < 1e-6, fit["metrics"]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        samples_npz = tmp_path / "calibration_samples.npz"
        out_json = tmp_path / "global_jones.json"

        np.savez_compressed(
            samples_npz,
            tx_jones=tx,
            rx_jones=rx,
            observed_gain=y_noisy,
            path_matrices=path,
        )

        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        proc = subprocess.run(
            [
                "python3",
                "scripts/fit_global_jones_matrix.py",
                "--samples-npz",
                str(samples_npz),
                "--ridge",
                "1e-6",
                "--output-json",
                str(out_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Global Jones calibration completed." in proc.stdout, proc.stdout
        j_cli = load_global_jones_matrix_json(str(out_json))
        rel_cli = np.linalg.norm(j_cli - j_true) / (np.linalg.norm(j_true) + 1e-12)
        assert rel_cli < 2e-3, rel_cli
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert "metrics" in payload
        assert "nmse" in payload["metrics"]

    print("Global Jones calibration validation passed.")


if __name__ == "__main__":
    run()

