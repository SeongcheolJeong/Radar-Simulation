#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path

import numpy as np

from avxsim.pipeline import run_hybrid_frames_pipeline


def _write_const_ffd(path: Path, gain: complex) -> None:
    lines = ["# theta phi et_re et_im ep_re ep_im"]
    for th in [0.0, 90.0, 180.0]:
        for ph in [0.0, 90.0, 180.0, 270.0]:
            lines.append(f"{th:.1f} {ph:.1f} {np.real(gain):.8f} {np.imag(gain):.8f} 0.0 0.0")
    path.write_text("\n".join(lines), encoding="utf-8")


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        frames_root = tmp_path / "frames"
        pair = frames_root / "Tx0Rx0"
        pair.mkdir(parents=True, exist_ok=True)

        amp = np.zeros((8, 8), dtype=np.float32)
        dist = np.zeros((8, 8), dtype=np.float32)
        amp[2, 3] = 1.0
        dist[2, 3] = 30.0
        np.save(pair / "AmplitudeOutput0001.npy", amp)
        np.save(pair / "DistanceOutput0001.npy", dist)

        radar_json = tmp_path / "radar_parameters_hybrid.json"
        radar_json.write_text(
            json.dumps(
                {
                    "antenna_offsets_tx": {"Tx0": [0, 0, 0], "Tx1": [0, -0.0078, 0]},
                    "antenna_offsets_rx": {
                        "Rx0": [0, 0.00185, 0],
                        "Rx1": [0, 0.0037, 0],
                        "Rx2": [0, 0.00555, 0],
                        "Rx3": [0, 0.0074, 0],
                    },
                }
            ),
            encoding="utf-8",
        )

        # isotropic baseline
        iso = run_hybrid_frames_pipeline(
            frames_root_dir=str(frames_root),
            radar_json_path=str(radar_json),
            frame_indices=[1],
            fc_hz=77e9,
            slope_hz_per_s=20e12,
            fs_hz=20e6,
            samples_per_chirp=1024,
            camera_fov_deg=90.0,
            mode="reflection",
            file_ext=".npy",
            output_dir=None,
        )
        adc_iso = iso["adc"]

        # constant-gain .ffd patterns
        ffd_dir = tmp_path / "ffd"
        ffd_dir.mkdir(parents=True, exist_ok=True)
        tx_file = ffd_dir / "tx0.ffd"
        _write_const_ffd(tx_file, gain=2.0 + 0.0j)
        rx_gains = [1.0, 0.5, 0.25, 0.125]
        rx_files = []
        for i, g in enumerate(rx_gains):
            p = ffd_dir / f"rx{i}.ffd"
            _write_const_ffd(p, gain=g + 0.0j)
            rx_files.append(str(p))

        ffd = run_hybrid_frames_pipeline(
            frames_root_dir=str(frames_root),
            radar_json_path=str(radar_json),
            frame_indices=[1],
            fc_hz=77e9,
            slope_hz_per_s=20e12,
            fs_hz=20e6,
            samples_per_chirp=1024,
            camera_fov_deg=90.0,
            mode="reflection",
            file_ext=".npy",
            tx_ffd_files=[str(tx_file)],
            rx_ffd_files=rx_files,
            ffd_field_format="real_imag",
            output_dir=None,
        )
        assert ffd["ffd_enabled"] is True
        adc_ffd = ffd["adc"]

        # chirp0 uses tx0 in current schedule for single-frame case.
        sig_iso = adc_iso[:, 0, 0, :]
        sig_ffd = adc_ffd[:, 0, 0, :]
        for rx_idx, g_rx in enumerate(rx_gains):
            ratio = np.mean(np.abs(sig_ffd[:, rx_idx])) / np.mean(np.abs(sig_iso[:, rx_idx]))
            expected = 2.0 * g_rx
            assert abs(ratio - expected) < 1e-3, (rx_idx, ratio, expected)

    print("FFD pipeline integration validation passed.")


if __name__ == "__main__":
    run()

