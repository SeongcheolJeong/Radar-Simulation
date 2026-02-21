#!/usr/bin/env python3
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from avxsim.antenna import FfdAntennaModel
from avxsim.calibration import load_global_jones_matrix_json
from avxsim.io import save_adc_npz, save_paths_by_chirp_json
from avxsim.synth import synth_fmcw_tdm
from avxsim.types import Path as RadarPath
from avxsim.types import RadarConfig


def _write_const_ffd(path: Path, etheta: complex, ephi: complex) -> None:
    lines = ["# theta phi et_re et_im ep_re ep_im"]
    for th in [0.0, 90.0, 180.0]:
        for ph in [0.0, 90.0, 180.0, 270.0]:
            lines.append(
                f"{th:.1f} {ph:.1f} "
                f"{np.real(etheta):.8f} {np.imag(etheta):.8f} "
                f"{np.real(ephi):.8f} {np.imag(ephi):.8f}"
            )
    path.write_text("\n".join(lines), encoding="utf-8")


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        ffd_dir = tmp_path / "ffd"
        ffd_dir.mkdir(parents=True, exist_ok=True)
        _write_const_ffd(ffd_dir / "tx0.ffd", etheta=1.0 + 0.0j, ephi=0.2 + 0.0j)
        _write_const_ffd(ffd_dir / "tx1.ffd", etheta=0.3 + 0.1j, ephi=1.0 + 0.0j)
        _write_const_ffd(ffd_dir / "rx0.ffd", etheta=1.0 + 0.2j, ephi=-0.1 + 0.0j)
        _write_const_ffd(ffd_dir / "rx1.ffd", etheta=0.2 + 0.1j, ephi=1.1 - 0.1j)

        ant = FfdAntennaModel.from_files(
            tx_ffd_files=[str(ffd_dir / "tx0.ffd"), str(ffd_dir / "tx1.ffd")],
            rx_ffd_files=[str(ffd_dir / "rx0.ffd"), str(ffd_dir / "rx1.ffd")],
            n_tx=2,
            n_rx=2,
            field_format="real_imag",
        )

        tx_pos = np.asarray([[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]], dtype=np.float64)
        rx_pos = np.asarray([[0.0, 0.00185, 0.0], [0.0, 0.0037, 0.0]], dtype=np.float64)
        tx_schedule = [i % 2 for i in range(12)]
        radar = RadarConfig(
            fc_hz=77e9,
            slope_hz_per_s=20e12,
            fs_hz=5e6,
            samples_per_chirp=512,
            tx_schedule=tx_schedule,
        )
        paths_by_chirp = []
        for k in range(len(tx_schedule)):
            paths_by_chirp.append(
                [
                    RadarPath(
                        delay_s=40e-9 + (k % 3) * 0.5e-9,
                        doppler_hz=0.0,
                        unit_direction=(1.0, 0.0, 0.0),
                        amp=1.0 + 0.0j,
                        pol_matrix=(1.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j, 1.0 + 0.0j),
                    )
                ]
            )

        j_true = np.asarray(
            [
                [1.15 + 0.15j, -0.08 + 0.02j],
                [0.05 - 0.03j, 0.9 - 0.05j],
            ],
            dtype=np.complex128,
        )
        adc = synth_fmcw_tdm(
            paths_by_chirp=paths_by_chirp,
            tx_pos_m=tx_pos,
            rx_pos_m=rx_pos,
            radar=radar,
            antenna_model=ant,
            use_jones_polarization=True,
            global_jones_matrix=j_true,
        )

        path_json = tmp_path / "path_list.json"
        adc_npz = tmp_path / "adc_cube.npz"
        save_paths_by_chirp_json(paths_by_chirp, str(path_json))
        save_adc_npz(adc, radar, tx_pos, rx_pos, str(adc_npz))

        samples_npz = tmp_path / "calibration_samples.npz"
        cmd_build = [
            "python3",
            "scripts/build_calibration_samples_from_outputs.py",
            "--path-list-json",
            str(path_json),
            "--adc-npz",
            str(adc_npz),
            "--tx-ffd-glob",
            str(ffd_dir / "tx*.ffd"),
            "--rx-ffd-glob",
            str(ffd_dir / "rx*.ffd"),
            "--ffd-field-format",
            "real_imag",
            "--observed-mode",
            "normalized",
            "--max-paths-per-chirp",
            "1",
            "--output-npz",
            str(samples_npz),
        ]
        proc_build = subprocess.run(
            cmd_build,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Calibration samples build completed." in proc_build.stdout, proc_build.stdout

        with np.load(samples_npz, allow_pickle=False) as s:
            assert s["tx_jones"].shape[0] == len(tx_schedule) * 2, s["tx_jones"].shape
            assert s["rx_jones"].shape == (len(tx_schedule) * 2, 2), s["rx_jones"].shape
            assert s["path_matrices"].shape == (len(tx_schedule) * 2, 2, 2), s["path_matrices"].shape

        fit_json = tmp_path / "global_jones_fit.json"
        cmd_fit = [
            "python3",
            "scripts/fit_global_jones_matrix.py",
            "--samples-npz",
            str(samples_npz),
            "--ridge",
            "1e-8",
            "--output-json",
            str(fit_json),
        ]
        proc_fit = subprocess.run(
            cmd_fit,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Global Jones calibration completed." in proc_fit.stdout, proc_fit.stdout

        j_hat = load_global_jones_matrix_json(str(fit_json))
        rel = np.linalg.norm(j_hat - j_true) / (np.linalg.norm(j_true) + 1e-12)
        assert rel < 1e-4, rel

    print("Calibration samples builder validation passed.")


if __name__ == "__main__":
    run()

