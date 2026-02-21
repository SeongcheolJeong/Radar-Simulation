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

        profile_json = tmp_path / "scenario_profile.json"
        profile_json.write_text(
            json.dumps(
                {
                    "version": 1,
                    "scenario_id": "moving_target_v1",
                    "created_utc": "2026-02-21T00:00:00+00:00",
                    "global_jones_matrix": [
                        {"re": 1.4, "im": 0.0},
                        {"re": 0.0, "im": 0.0},
                        {"re": 0.0, "im": 0.0},
                        {"re": 1.0, "im": 0.0},
                    ],
                    "parity_thresholds": {"ra_peak_angle_bin_abs_error_max": 2.0},
                    "motion_compensation_defaults": {
                        "enabled": True,
                        "fd_hz": 0.0,
                        "chirp_interval_s": 6e-5,
                        "reference_tx": 0,
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
            "--scenario-profile-json",
            str(profile_json),
            "--run-hybrid-estimation",
            "--output-dir",
            str(out_dir),
        ]
        proc = subprocess.run(
            cmd,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "scenario profile enabled: True" in proc.stdout, proc.stdout
        assert "global jones enabled: True" in proc.stdout, proc.stdout
        assert "motion compensation enabled: True" in proc.stdout, proc.stdout
        assert "motion compensation fd_hz: 0.0" in proc.stdout, proc.stdout
        assert (out_dir / "hybrid_estimation.npz").exists()
        print("Hybrid ingest CLI with profile defaults validation passed.")


if __name__ == "__main__":
    run()

