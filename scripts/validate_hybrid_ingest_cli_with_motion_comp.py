#!/usr/bin/env python3
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        frames_root = tmp_path / "frames"
        pair = frames_root / "Tx0Rx0"
        pair.mkdir(parents=True, exist_ok=True)

        # Two-frame minimal input to exercise estimation path.
        for idx, (dist_m, amp) in enumerate([(30.0, 1.0), (31.0, 0.9)], start=1):
            amp_map = np.zeros((8, 8), dtype=np.float32)
            dist_map = np.zeros((8, 8), dtype=np.float32)
            amp_map[2 + idx, 3] = amp
            dist_map[2 + idx, 3] = dist_m
            np.save(pair / f"AmplitudeOutput{idx:04d}.npy", amp_map)
            np.save(pair / f"DistanceOutput{idx:04d}.npy", dist_map)

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
            "2",
            "--camera-fov-deg",
            "90",
            "--mode",
            "reflection",
            "--file-ext",
            ".npy",
            "--run-hybrid-estimation",
            "--enable-motion-compensation",
            "--motion-comp-fd-hz",
            "0.0",
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

        assert "motion compensation enabled: True" in proc.stdout, proc.stdout
        assert "motion compensation fd_hz: 0.0" in proc.stdout, proc.stdout
        assert (out_dir / "path_list.json").exists()
        assert (out_dir / "adc_cube.npz").exists()
        assert (out_dir / "hybrid_estimation.npz").exists()
        print("Hybrid ingest CLI with motion compensation validation passed.")


if __name__ == "__main__":
    run()

