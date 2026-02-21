#!/usr/bin/env python3
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from avxsim.calibration import load_global_jones_matrix_json
from avxsim.scenario_profile import load_scenario_profile_json


def _gaussian2d(shape, c0, c1, s0, s1, amp):
    y = np.arange(shape[0], dtype=np.float64)[:, None]
    x = np.arange(shape[1], dtype=np.float64)[None, :]
    z = np.exp(-0.5 * (((y - c0) / s0) ** 2 + ((x - c1) / s1) ** 2))
    return amp * z


def _make_estimation_npz(path, rd, ra):
    np.savez_compressed(path, fx_dop_win=rd, fx_ang=ra)


def run() -> None:
    rng = np.random.default_rng(11)
    n = 220
    tx = rng.normal(size=(n, 2)) + 1j * rng.normal(size=(n, 2))
    rx = rng.normal(size=(n, 2)) + 1j * rng.normal(size=(n, 2))
    path = rng.normal(size=(n, 2, 2)) + 1j * rng.normal(size=(n, 2, 2))
    for i in range(n):
        path[i, :, :] += np.eye(2)

    j_true = np.asarray(
        [
            [1.06 + 0.12j, -0.09 + 0.03j],
            [0.04 - 0.02j, 0.95 - 0.06j],
        ],
        dtype=np.complex128,
    )
    obs = np.einsum("ni,ij,njk,nk->n", np.conj(rx), j_true, path, tx)
    obs += (rng.normal(size=n) + 1j * rng.normal(size=n)) * 1e-5

    rd_ref = _gaussian2d((96, 128), 41.0, 64.0, 6.5, 8.0, 10.0)
    ra_ref = _gaussian2d((96, 128), 54.0, 62.0, 7.0, 6.0, 7.0)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        samples_npz = tmp_path / "samples.npz"
        np.savez_compressed(
            samples_npz,
            tx_jones=tx,
            rx_jones=rx,
            observed_gain=obs,
            path_matrices=path,
        )

        ref_npz = tmp_path / "reference_hybrid_estimation.npz"
        _make_estimation_npz(ref_npz, rd_ref, ra_ref)

        train_npz = []
        for i, shift in enumerate([0, 1, -1], start=1):
            rd = np.roll(rd_ref * (1.0 + 0.01 * i), shift=shift, axis=0)
            ra = np.roll(ra_ref * (1.0 - 0.01 * i), shift=shift, axis=0)
            p = tmp_path / f"train_{i}.npz"
            _make_estimation_npz(p, rd, ra)
            train_npz.append(p)

        good_npz = tmp_path / "good_candidate.npz"
        bad_npz = tmp_path / "bad_candidate.npz"
        _make_estimation_npz(
            good_npz,
            np.roll(rd_ref * 1.015, shift=1, axis=0),
            np.roll(ra_ref * 0.99, shift=1, axis=0),
        )
        _make_estimation_npz(
            bad_npz,
            np.roll(rd_ref, shift=12, axis=0),
            np.roll(ra_ref, shift=-10, axis=0),
        )

        profile_json = tmp_path / "scenario_profile.json"
        cmd_build = [
            "python3",
            "scripts/build_scenario_profile.py",
            "--scenario-id",
            "chamber_static_v1",
            "--samples-npz",
            str(samples_npz),
            "--reference-estimation-npz",
            str(ref_npz),
            "--threshold-quantile",
            "0.95",
            "--threshold-margin",
            "2.0",
            "--output-profile-json",
            str(profile_json),
        ]
        for p in train_npz:
            cmd_build.extend(["--train-estimation-npz", str(p)])
        proc_build = subprocess.run(
            cmd_build,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Scenario profile build completed." in proc_build.stdout, proc_build.stdout
        profile = load_scenario_profile_json(str(profile_json))
        j_hat = load_global_jones_matrix_json(str(profile_json))
        rel = np.linalg.norm(j_hat - j_true) / (np.linalg.norm(j_true) + 1e-12)
        assert rel < 4e-4, rel
        assert profile["scenario_id"] == "chamber_static_v1"
        assert "parity_thresholds" in profile
        assert len(profile["parity_thresholds"]) > 0
        assert "reference_estimation_npz" in profile

        proc_good = subprocess.run(
            [
                "python3",
                "scripts/evaluate_scenario_profile.py",
                "--profile-json",
                str(profile_json),
                "--candidate-estimation-npz",
                str(good_npz),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc_good.returncode == 0, proc_good.stdout + "\n" + proc_good.stderr
        assert "parity pass: True" in proc_good.stdout, proc_good.stdout

        proc_bad = subprocess.run(
            [
                "python3",
                "scripts/evaluate_scenario_profile.py",
                "--profile-json",
                str(profile_json),
                "--candidate-estimation-npz",
                str(bad_npz),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc_bad.returncode == 2, proc_bad.stdout + "\n" + proc_bad.stderr
        assert "parity pass: False" in proc_bad.stdout, proc_bad.stdout

    print("Scenario profile workflow validation passed.")


if __name__ == "__main__":
    run()

