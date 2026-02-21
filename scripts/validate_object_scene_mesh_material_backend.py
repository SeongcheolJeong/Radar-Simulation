#!/Library/Developer/CommandLineTools/usr/bin/python3
import json
import tempfile
from pathlib import Path

import numpy as np

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_scene_mesh_material_") as td:
        root = Path(td)
        scene_json = root / "scene_mesh_material.json"
        scene_json.write_text(
            json.dumps(
                {
                    "scene_id": "mesh_material_scene_v1",
                    "backend": {
                        "type": "mesh_material_stub",
                        "n_chirps": 6,
                        "chirp_interval_s": 4.0e-5,
                        "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                        "rx_pos_m": [
                            [0.0, 0.00185, 0.0],
                            [0.0, 0.0037, 0.0],
                            [0.0, 0.00555, 0.0],
                            [0.0, 0.0074, 0.0],
                        ],
                        "ego_pos_m": [0.0, 0.0, 0.0],
                        "range_amp_exponent": 2.0,
                        "materials": {
                            "metal": {"reflectivity": 0.9, "attenuation_db": 1.0},
                            "plastic": {"reflectivity": 0.25, "attenuation_db": 6.0},
                        },
                        "objects": [
                            {
                                "object_id": "car_body",
                                "centroid_m": [25.0, 0.5, 0.0],
                                "velocity_mps": [2.0, 0.0, 0.0],
                                "material_tag": "metal",
                                "mesh_area_m2": 8.0,
                                "rcs_scale": 1.0,
                                "reflection_order": 1,
                            },
                            {
                                "object_id": "traffic_cone",
                                "centroid_m": [18.0, -1.2, 0.0],
                                "radial_velocity_mps": 0.0,
                                "material_tag": "plastic",
                                "mesh_area_m2": 0.6,
                                "rcs_scale": 0.5,
                                "reflection_order": 2,
                            },
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

        out_dir = root / "outputs"
        out = run_object_scene_to_radar_map_json(
            scene_json_path=str(scene_json),
            output_dir=str(out_dir),
            run_hybrid_estimation=False,
        )

        assert (out_dir / "path_list.json").exists()
        assert (out_dir / "adc_cube.npz").exists()
        assert (out_dir / "radar_map.npz").exists()
        assert out["hybrid_estimation_npz"] is None
        assert out["frame_count"] == 6

        paths_payload = json.loads((out_dir / "path_list.json").read_text(encoding="utf-8"))
        assert isinstance(paths_payload, list) and len(paths_payload) == 6
        assert len(paths_payload[0]) == 2
        tags = {str(p["material_tag"]) for p in paths_payload[0]}
        assert "metal" in tags and "plastic" in tags
        for p in paths_payload[0]:
            assert "path_id" in p
            assert "reflection_order" in p

        # Material-ordered reflection metadata check.
        cone = [p for p in paths_payload[0] if "traffic_cone" in str(p["path_id"])]
        assert len(cone) == 1
        assert int(cone[0]["reflection_order"]) == 2

        adc_payload = np.load(out_dir / "adc_cube.npz")
        adc = np.asarray(adc_payload["adc"])
        assert adc.shape == (1024, 6, 2, 4), adc.shape

        map_payload = np.load(out_dir / "radar_map.npz")
        rd = np.asarray(map_payload["fx_dop_win"])
        ra = np.asarray(map_payload["fx_ang"])
        assert rd.shape == (64, 128), rd.shape
        assert ra.shape == (32, 128), ra.shape
        meta = json.loads(str(map_payload["metadata_json"]))
        assert meta["backend_type"] == "mesh_material_stub"

    print("validate_object_scene_mesh_material_backend: pass")


if __name__ == "__main__":
    run()
