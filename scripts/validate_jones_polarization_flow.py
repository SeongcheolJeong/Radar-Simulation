#!/usr/bin/env python3
import tempfile
from pathlib import Path

import numpy as np

from avxsim.antenna import FfdAntennaModel
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
        tx_ffd = tmp_path / "tx0.ffd"
        rx_ffd = tmp_path / "rx0.ffd"

        tx_j = np.asarray([1.0 + 1.0j, 2.0 - 1.0j], dtype=np.complex128)
        rx_j = np.asarray([0.5 + 0.25j, -0.75 + 0.5j], dtype=np.complex128)
        _write_const_ffd(tx_ffd, etheta=tx_j[0], ephi=tx_j[1])
        _write_const_ffd(rx_ffd, etheta=rx_j[0], ephi=rx_j[1])

        ant = FfdAntennaModel.from_files(
            tx_ffd_files=[str(tx_ffd)],
            rx_ffd_files=[str(rx_ffd)],
            n_tx=1,
            n_rx=1,
            field_format="real_imag",
        )

        j_path = np.asarray(
            [
                [1.0 + 0.0j, 0.0 + 0.2j],
                [0.0 + 0.0j, 0.5 + 0.0j],
            ],
            dtype=np.complex128,
        )
        path = RadarPath(
            delay_s=0.0,
            doppler_hz=0.0,
            unit_direction=(1.0, 0.0, 0.0),  # az=0, el=0 -> theta=90, phi=0
            amp=1.0 + 0.0j,
            pol_matrix=tuple(j_path.reshape(-1)),
        )

        radar = RadarConfig(
            fc_hz=77e9,
            slope_hz_per_s=0.0,
            fs_hz=10e6,
            samples_per_chirp=128,
            tx_schedule=[0],
        )
        tx_pos = np.zeros((1, 3), dtype=np.float64)
        rx_pos = np.zeros((1, 3), dtype=np.float64)

        adc = synth_fmcw_tdm(
            paths_by_chirp=[[path]],
            tx_pos_m=tx_pos,
            rx_pos_m=rx_pos,
            radar=radar,
            antenna_model=ant,
            use_jones_polarization=True,
        )

        expected_gain = np.conj(rx_j) @ j_path @ tx_j
        sig = adc[:, 0, 0, 0]
        mean_sig = np.mean(sig)
        assert np.allclose(sig, mean_sig, atol=1e-6)
        assert abs(mean_sig - expected_gain) < 1e-5, (mean_sig, expected_gain)
        print("Jones polarization flow validation passed.")


if __name__ == "__main__":
    run()

