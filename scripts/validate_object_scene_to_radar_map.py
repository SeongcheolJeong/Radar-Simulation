#!/Library/Developer/CommandLineTools/usr/bin/python3
import json
import tempfile
from pathlib import Path

import numpy as np

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        frames_root = tmp_path / "frames"
        pair = frames_root / "Tx0Rx0"
        pair.mkdir(parents=True, exist_ok=True)

        # Create simple frame maps with one active reflector per chirp.
        for idx, (rtt_dist, amp) in enumerate([(22.0, 1.0), (24.0, 0.8), (26.0, 0.6)], start=1):
            amp_map = np.zeros((8, 8), dtype=np.float32)
            dist_map = np.zeros((8, 8), dtype=np.float32)
            amp_map[2 + idx, 3] = amp
            dist_map[2 + idx, 3] = rtt_dist
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

        scene_json = tmp_path / "scene.json"
        scene_json.write_text(
            json.dumps(
                {
                    "scene_id": "mock_scene_v1",
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

        out_dir = tmp_path / "outputs"
        result = run_object_scene_to_radar_map_json(
            scene_json_path=str(scene_json),
            output_dir=str(out_dir),
            run_hybrid_estimation=True,
        )

        assert (out_dir / "path_list.json").exists()
        assert (out_dir / "adc_cube.npz").exists()
        assert (out_dir / "radar_map.npz").exists()
        assert (out_dir / "hybrid_estimation.npz").exists()

        adc_payload = np.load(out_dir / "adc_cube.npz")
        adc = np.asarray(adc_payload["adc"])
        assert adc.shape == (1024, 3, 2, 4), adc.shape

        paths_payload = json.loads((out_dir / "path_list.json").read_text(encoding="utf-8"))
        assert isinstance(paths_payload, list) and len(paths_payload) == 3
        first_path = paths_payload[0][0]
        assert "path_id" in first_path
        assert first_path["material_tag"] == "reflection"
        assert first_path["reflection_order"] == 1

        map_payload = np.load(out_dir / "radar_map.npz")
        rd = np.asarray(map_payload["fx_dop_win"])
        ra = np.asarray(map_payload["fx_ang"])
        assert rd.shape == (64, 128), rd.shape
        assert ra.shape == (32, 128), ra.shape
        meta = json.loads(str(map_payload["metadata_json"]))
        assert meta["scene_id"] == "mock_scene_v1"
        assert meta["backend_type"] == "hybrid_frames"

        assert result["frame_count"] == 3
        assert str(out_dir / "radar_map.npz") == result["radar_map_npz"]
        print("Object scene to radar map validation passed.")


if __name__ == "__main__":
    run()
