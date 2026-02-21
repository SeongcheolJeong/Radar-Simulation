#!/usr/bin/env python3
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np


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

        ffd_dir = tmp_path / "ffd"
        ffd_dir.mkdir(parents=True, exist_ok=True)
        _write_const_ffd(ffd_dir / "tx0.ffd", gain=1.5 + 0.0j)
        for i in range(4):
            _write_const_ffd(ffd_dir / f"rx{i}.ffd", gain=1.0 + 0.0j)

        out_dir = tmp_path / "outputs"
        cmd = [
            "python3",
            "scripts/run_hybrid_ingest_to_adc.py",
            "--frames-root",
            str(frames_root),
            "--radar-json",
            str(radar_json),
            "--frame-start",
            "1",
            "--frame-end",
            "1",
            "--camera-fov-deg",
            "90",
            "--mode",
            "reflection",
            "--file-ext",
            ".npy",
            "--tx-ffd-glob",
            str(ffd_dir / "tx*.ffd"),
            "--rx-ffd-glob",
            str(ffd_dir / "rx*.ffd"),
            "--ffd-field-format",
            "real_imag",
            "--use-jones-polarization",
            "--output-dir",
            str(out_dir),
        ]
        proc = subprocess.run(
            cmd,
            cwd=str(Path(__file__).resolve().parents[1]),
            capture_output=True,
            text=True,
            check=True,
        )
        assert "ffd enabled: True" in proc.stdout, proc.stdout
        assert "jones polarization enabled: True" in proc.stdout, proc.stdout
        assert (out_dir / "path_list.json").exists()
        assert (out_dir / "adc_cube.npz").exists()
        print("Hybrid ingest CLI with FFD validation passed.")


if __name__ == "__main__":
    run()
