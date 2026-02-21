#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        frames_root = tmp_path / "frames"
        pair = frames_root / "Tx0Rx0"
        pair.mkdir(parents=True, exist_ok=True)

        amp = np.zeros((8, 8), dtype=np.float32)
        dist = np.zeros((8, 8), dtype=np.float32)
        amp[3, 4] = 1.0
        dist[3, 4] = 30.0
        np.save(pair / "AmplitudeOutput0001.npy", amp)
        np.save(pair / "DistanceOutput0001.npy", dist)

        radar_json = tmp_path / "radar_parameters_hybrid.json"
        radar_json.write_text(
            json.dumps(
                {
                    "antenna_offsets_tx": {"Tx0": [0, 0, 0]},
                    "antenna_offsets_rx": {"Rx0": [0, 0.00185, 0]},
                }
            ),
            encoding="utf-8",
        )

        out_base = tmp_path / "out_base"
        cmd_base = [
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
            "--use-jones-polarization",
            "--output-dir",
            str(out_base),
        ]
        proc_base = subprocess.run(
            cmd_base,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "global jones enabled: False" in proc_base.stdout, proc_base.stdout

        global_json = tmp_path / "global_jones.json"
        global_json.write_text(
            json.dumps(
                {
                    "global_jones_matrix": [
                        {"re": 1.8, "im": 0.0},
                        {"re": 0.0, "im": 0.0},
                        {"re": 0.0, "im": 0.0},
                        {"re": 1.0, "im": 0.0},
                    ]
                }
            ),
            encoding="utf-8",
        )

        out_cal = tmp_path / "out_cal"
        cmd_cal = [
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
            "--global-jones-json",
            str(global_json),
            "--output-dir",
            str(out_cal),
        ]
        proc_cal = subprocess.run(
            cmd_cal,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "global jones enabled: True" in proc_cal.stdout, proc_cal.stdout
        assert "jones polarization enabled: True" in proc_cal.stdout, proc_cal.stdout

        adc_base = np.load(out_base / "adc_cube.npz", allow_pickle=False)["adc"]
        adc_cal = np.load(out_cal / "adc_cube.npz", allow_pickle=False)["adc"]
        mag_base = float(np.mean(np.abs(adc_base)))
        mag_cal = float(np.mean(np.abs(adc_cal)))
        ratio = mag_cal / (mag_base + 1e-12)
        assert abs(ratio - 1.8) < 1e-2, ratio

    print("Hybrid ingest CLI with global Jones validation passed.")


if __name__ == "__main__":
    run()

