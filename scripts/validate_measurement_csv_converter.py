#!/usr/bin/env python3
import csv
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from avxsim.calibration import fit_global_jones_matrix, load_global_jones_matrix_json
from avxsim.calibration_samples import load_calibration_samples_npz
from avxsim.measurement_csv import convert_measurement_csv_to_npz


def _make_row(
    tx,
    rx,
    obs,
    pmat,
    chirp_idx,
    tx_idx,
    rx_idx,
    path_idx,
    frame_idx,
):
    return {
        "tx_theta_re": float(np.real(tx[0])),
        "tx_theta_im": float(np.imag(tx[0])),
        "tx_phi_re": float(np.real(tx[1])),
        "tx_phi_im": float(np.imag(tx[1])),
        "rx_theta_re": float(np.real(rx[0])),
        "rx_theta_im": float(np.imag(rx[0])),
        "rx_phi_re": float(np.real(rx[1])),
        "rx_phi_im": float(np.imag(rx[1])),
        "observed_re": float(np.real(obs)),
        "observed_im": float(np.imag(obs)),
        "path_m00_re": float(np.real(pmat[0, 0])),
        "path_m00_im": float(np.imag(pmat[0, 0])),
        "path_m01_re": float(np.real(pmat[0, 1])),
        "path_m01_im": float(np.imag(pmat[0, 1])),
        "path_m10_re": float(np.real(pmat[1, 0])),
        "path_m10_im": float(np.imag(pmat[1, 0])),
        "path_m11_re": float(np.real(pmat[1, 1])),
        "path_m11_im": float(np.imag(pmat[1, 1])),
        "chirp_idx": int(chirp_idx),
        "tx_idx": int(tx_idx),
        "rx_idx": int(rx_idx),
        "path_idx": int(path_idx),
        "frame_idx": int(frame_idx),
    }


def run() -> None:
    rng = np.random.default_rng(7)
    n = 180
    tx = rng.normal(size=(n, 2)) + 1j * rng.normal(size=(n, 2))
    rx = rng.normal(size=(n, 2)) + 1j * rng.normal(size=(n, 2))
    pmat = rng.normal(size=(n, 2, 2)) + 1j * rng.normal(size=(n, 2, 2))
    for i in range(n):
        pmat[i, :, :] += np.eye(2)

    j_true = np.asarray(
        [
            [1.04 + 0.13j, -0.11 + 0.04j],
            [0.07 - 0.02j, 0.92 - 0.08j],
        ],
        dtype=np.complex128,
    )
    obs = np.einsum("ni,ij,njk,nk->n", np.conj(rx), j_true, pmat, tx)
    obs += (rng.normal(size=n) + 1j * rng.normal(size=n)) * 1e-5

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        csv_path = tmp_path / "measurement.csv"
        out_npz = tmp_path / "calibration_samples.npz"
        fit_json = tmp_path / "global_jones_fit.json"
        col_map_json = tmp_path / "column_map.json"

        rows = []
        for i in range(n):
            rows.append(
                _make_row(
                    tx=tx[i],
                    rx=rx[i],
                    obs=obs[i],
                    pmat=pmat[i],
                    chirp_idx=i % 32,
                    tx_idx=i % 2,
                    rx_idx=i % 4,
                    path_idx=i % 3,
                    frame_idx=i // 32,
                )
            )
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        # Direct API conversion
        samples = convert_measurement_csv_to_npz(
            csv_path=str(csv_path),
            out_npz=str(out_npz),
        )
        assert samples["tx_jones"].shape == (n, 2), samples["tx_jones"].shape
        assert samples["path_matrices"].shape == (n, 2, 2), samples["path_matrices"].shape
        loaded = load_calibration_samples_npz(str(out_npz))
        assert loaded["observed_gain"].shape == (n,), loaded["observed_gain"].shape
        assert loaded["chirp_idx"].shape == (n,), loaded["chirp_idx"].shape

        fit = fit_global_jones_matrix(
            tx_jones=loaded["tx_jones"],
            rx_jones=loaded["rx_jones"],
            observed_gain=loaded["observed_gain"],
            path_matrices=loaded["path_matrices"],
            ridge=1e-8,
        )
        j_hat = np.asarray(fit["global_jones_matrix"], dtype=np.complex128)
        rel = np.linalg.norm(j_hat - j_true) / (np.linalg.norm(j_true) + 1e-12)
        assert rel < 3e-4, rel

        # CLI conversion with column map override
        # remap one column name to verify map path.
        mapped_csv = tmp_path / "measurement_mapped.csv"
        rows2 = []
        for r in rows:
            rr = dict(r)
            rr["obs_re_custom"] = rr.pop("observed_re")
            rows2.append(rr)
        with mapped_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows2[0].keys()))
            writer.writeheader()
            writer.writerows(rows2)
        col_map_json.write_text(json.dumps({"observed_re": "obs_re_custom"}), encoding="utf-8")

        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")
        cli_npz = tmp_path / "calibration_samples_cli.npz"
        proc = subprocess.run(
            [
                "python3",
                "scripts/build_calibration_samples_from_measurement_csv.py",
                "--input-csv",
                str(mapped_csv),
                "--output-npz",
                str(cli_npz),
                "--column-map-json",
                str(col_map_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Measurement CSV conversion completed." in proc.stdout, proc.stdout

        proc_fit = subprocess.run(
            [
                "python3",
                "scripts/fit_global_jones_matrix.py",
                "--samples-npz",
                str(cli_npz),
                "--ridge",
                "1e-8",
                "--output-json",
                str(fit_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Global Jones calibration completed." in proc_fit.stdout, proc_fit.stdout
        j_cli = load_global_jones_matrix_json(str(fit_json))
        rel_cli = np.linalg.norm(j_cli - j_true) / (np.linalg.norm(j_true) + 1e-12)
        assert rel_cli < 3e-4, rel_cli

    print("Measurement CSV converter validation passed.")


if __name__ == "__main__":
    run()

