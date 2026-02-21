#!/usr/bin/env python3
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from avxsim.parity import compare_hybrid_estimation_npz


def _gaussian2d(
    shape,
    center0: float,
    center1: float,
    sigma0: float,
    sigma1: float,
    amplitude: float,
) -> np.ndarray:
    y = np.arange(shape[0], dtype=np.float64)[:, None]
    x = np.arange(shape[1], dtype=np.float64)[None, :]
    z = np.exp(
        -0.5 * (((y - float(center0)) / float(sigma0)) ** 2 + ((x - float(center1)) / float(sigma1)) ** 2)
    )
    return float(amplitude) * z


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        ref_path = tmp_path / "reference.npz"
        cand_good_path = tmp_path / "candidate_good.npz"
        cand_bad_path = tmp_path / "candidate_bad.npz"

        rd_ref = _gaussian2d((96, 128), center0=41, center1=65, sigma0=6.5, sigma1=8.0, amplitude=10.0)
        ra_ref = _gaussian2d((96, 128), center0=52, center1=63, sigma0=7.0, sigma1=6.0, amplitude=7.5)

        rd_good = np.roll(rd_ref * 1.03, shift=1, axis=0)
        ra_good = np.roll(ra_ref * 0.98, shift=1, axis=0)

        rd_bad = np.roll(rd_ref, shift=12, axis=0)
        ra_bad = np.roll(ra_ref, shift=-9, axis=0)

        np.savez_compressed(ref_path, fx_dop_win=rd_ref, fx_ang=ra_ref)
        np.savez_compressed(cand_good_path, fx_dop_win=rd_good, fx_ang=ra_good)
        np.savez_compressed(cand_bad_path, fx_dop_win=rd_bad, fx_ang=ra_bad)

        report_good = compare_hybrid_estimation_npz(str(ref_path), str(cand_good_path))
        assert report_good["pass"], report_good

        report_bad = compare_hybrid_estimation_npz(str(ref_path), str(cand_bad_path))
        assert not report_bad["pass"], report_bad
        assert len(report_bad["failures"]) > 0

        cmd = [
            "python3",
            "scripts/compare_hybrid_estimation_parity.py",
            "--reference-npz",
            str(ref_path),
            "--candidate-npz",
            str(cand_bad_path),
        ]
        proc = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 2, proc.stdout + "\n" + proc.stderr
        assert "parity pass: False" in proc.stdout, proc.stdout
        print("Parity metrics contract validation passed.")


if __name__ == "__main__":
    run()

