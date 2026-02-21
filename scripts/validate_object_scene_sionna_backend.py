#!/usr/bin/env python3
import json
import os
import tempfile
from pathlib import Path

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_scene_sionna_backend_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        os.environ.setdefault("PYTHONPATH", str(repo_root / "src"))

        sionna_paths_json = root / "sionna_paths.json"
        sionna_paths_json.write_text(
            json.dumps(
                {
                    "version": 1,
                    "paths": [
                        {
                            "chirp_index": 0,
                            "delay_s": 2.0 * 25.0 / 299_792_458.0,
                            "doppler_hz": 0.0,
                            "unit_direction": [1.0, 0.0, 0.0],
                            "amp": 0.0016,
                            "path_id": "sionna_path_0",
                            "material_tag": "metal",
                            "reflection_order": 1,
                        },
                        {
                            "chirp_index": 1,
                            "delay_s": 2.0 * 25.0 / 299_792_458.0,
                            "doppler_hz": 0.0,
                            "unit_direction": [1.0, 0.0, 0.0],
                            "amp_complex": {"re": 0.0016, "im": 0.0},
                            "path_id": "sionna_path_1",
                            "material_tag": "metal",
                            "reflection_order": 1,
                        },
                        {
                            "chirp_index": 2,
                            "delay_s": 2.0 * 25.0 / 299_792_458.0,
                            "doppler_hz": 0.0,
                            "u": [1.0, 0.0, 0.0],
                            "amp": [0.0016, 0.0],
                            "path_id": "sionna_path_2",
                            "material_tag": "metal",
                            "reflection_order": 1,
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        scene_json = root / "scene_sionna.json"
        scene_json.write_text(
            json.dumps(
                {
                    "scene_id": "sionna_scene_v1",
                    "backend": {
                        "type": "sionna_rt",
                        "n_chirps": 3,
                        "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                        "rx_pos_m": [
                            [0.0, 0.00185, 0.0],
                            [0.0, 0.0037, 0.0],
                            [0.0, 0.00555, 0.0],
                            [0.0, 0.0074, 0.0],
                        ],
                        "sionna_paths_json": str(sionna_paths_json),
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

        out_dir = root / "outputs"
        out = run_object_scene_to_radar_map_json(
            scene_json_path=str(scene_json),
            output_dir=str(out_dir),
            run_hybrid_estimation=False,
        )
        assert out["frame_count"] == 3
        assert (out_dir / "path_list.json").exists()
        assert (out_dir / "adc_cube.npz").exists()
        assert (out_dir / "radar_map.npz").exists()

        path_payload = json.loads((out_dir / "path_list.json").read_text(encoding="utf-8"))
        assert len(path_payload) == 3
        assert path_payload[0][0]["path_id"] == "sionna_path_0"
        assert path_payload[1][0]["path_id"] == "sionna_path_1"
        assert path_payload[2][0]["path_id"] == "sionna_path_2"

    print("validate_object_scene_sionna_backend: pass")


if __name__ == "__main__":
    run()
