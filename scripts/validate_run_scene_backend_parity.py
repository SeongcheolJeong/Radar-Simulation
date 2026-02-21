#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def _write_hybrid_scene(root: Path) -> Path:
    frames_root = root / "hybrid_frames"
    pair = frames_root / "Tx0Rx0"
    pair.mkdir(parents=True, exist_ok=True)

    for idx, (rtt_dist, amp) in enumerate([(22.0, 1.0), (24.0, 0.8), (26.0, 0.6)], start=1):
        amp_map = np.zeros((8, 8), dtype=np.float32)
        dist_map = np.zeros((8, 8), dtype=np.float32)
        amp_map[2 + idx, 3] = amp
        dist_map[2 + idx, 3] = rtt_dist
        np.save(pair / f"AmplitudeOutput{idx:04d}.npy", amp_map)
        np.save(pair / f"DistanceOutput{idx:04d}.npy", dist_map)

    radar_json = root / "hybrid_radar_parameters.json"
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

    scene_json = root / "scene_hybrid.json"
    scene_json.write_text(
        json.dumps(
            {
                "scene_id": "parity_hybrid_scene",
                "backend": {
                    "type": "hybrid_frames",
                    "frames_root_dir": str(frames_root),
                    "radar_json_path": str(radar_json),
                    "frame_indices": [1, 2, 3],
                    "camera_fov_deg": 90.0,
                    "mode": "reflection",
                    "file_ext": ".npy",
                    "amplitude_threshold": 0.01,
                    "top_k_per_chirp": 1,
                },
                "radar": {
                    "fc_hz": 77e9,
                    "slope_hz_per_s": 20e12,
                    "fs_hz": 20e6,
                    "samples_per_chirp": 1024,
                },
                "map_config": {
                    "nfft_range": 1024,
                    "nfft_doppler": 64,
                    "nfft_angle": 32,
                    "range_bin_limit": 128,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return scene_json


def _write_analytic_scene(root: Path) -> Path:
    scene_json = root / "scene_analytic.json"
    scene_json.write_text(
        json.dumps(
            {
                "scene_id": "parity_analytic_scene",
                "backend": {
                    "type": "analytic_targets",
                    "n_chirps": 3,
                    "chirp_interval_s": 4.0e-5,
                    "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                    "rx_pos_m": [
                        [0.0, 0.00185, 0.0],
                        [0.0, 0.0037, 0.0],
                        [0.0, 0.00555, 0.0],
                        [0.0, 0.0074, 0.0],
                    ],
                    "targets": [
                        {
                            "range_m": 25.0,
                            "radial_velocity_mps": 0.0,
                            "az_deg": 0.0,
                            "el_deg": 0.0,
                            "amp": 1.0,
                            "range_amp_exponent": 2.0,
                        }
                    ],
                    "noise_sigma": 0.0,
                },
                "radar": {
                    "fc_hz": 77e9,
                    "slope_hz_per_s": 20e12,
                    "fs_hz": 20e6,
                    "samples_per_chirp": 1024,
                },
                "map_config": {
                    "nfft_range": 1024,
                    "nfft_doppler": 64,
                    "nfft_angle": 32,
                    "range_bin_limit": 128,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return scene_json


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_scene_backend_parity_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        ref_scene = _write_hybrid_scene(root)
        cand_scene = _write_analytic_scene(root)
        out_root = root / "parity_run"
        out_json = out_root / "parity_summary.json"

        proc = subprocess.run(
            [
                "python3",
                "scripts/run_scene_backend_parity.py",
                "--reference-scene-json",
                str(ref_scene),
                "--candidate-scene-json",
                str(cand_scene),
                "--allow-failures",
                "--output-root",
                str(out_root),
                "--output-summary-json",
                str(out_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Scene backend parity completed." in proc.stdout, proc.stdout

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["reference_backend_type"] == "hybrid_frames"
        assert payload["candidate_backend_type"] == "analytic_targets"
        parity = payload["parity"]
        assert "metrics" in parity and isinstance(parity["metrics"], dict)
        assert "pass" in parity

    print("validate_run_scene_backend_parity: pass")


if __name__ == "__main__":
    run()
