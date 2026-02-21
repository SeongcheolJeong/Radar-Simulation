#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_mesh_scene_bridge_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        asset_manifest = root / "asset_manifest.json"
        asset_manifest.write_text(
            json.dumps(
                {
                    "scene_id": "asset_bridge_scene",
                    "sensor_mount": {
                        "tx_pos_m": [[0.0, 0.0, 0.0], [0.0, -0.0078, 0.0]],
                        "rx_pos_m": [
                            [0.0, 0.00185, 0.0],
                            [0.0, 0.0037, 0.0],
                            [0.0, 0.00555, 0.0],
                            [0.0, 0.0074, 0.0],
                        ],
                        "ego_pos_m": [0.0, 0.0, 0.0],
                    },
                    "simulation_defaults": {
                        "n_chirps": 5,
                        "chirp_interval_s": 4.0e-5,
                        "range_amp_exponent": 2.0,
                        "noise_sigma": 0.0,
                    },
                    "radar": {
                        "fc_hz": 77e9,
                        "slope_hz_per_s": 20e12,
                        "fs_hz": 20e6,
                        "samples_per_chirp": 1024,
                    },
                    "materials": [
                        {"material_tag": "metal", "reflectivity": 0.9, "attenuation_db": 1.0},
                        {"material_tag": "asphalt", "reflectivity": 0.2, "attenuation_db": 8.0},
                    ],
                    "objects": [
                        {
                            "id": "car_a",
                            "bbox_center_m": [24.0, 0.5, 0.0],
                            "velocity_mps": [2.0, 0.0, 0.0],
                            "material": "metal",
                            "mesh_area": 7.5,
                            "rcs_scale": 1.0,
                            "reflection_order": 1,
                            "source_mesh_uri": "meshes/car_a.glb",
                        },
                        {
                            "object_id": "road_patch",
                            "centroid_m": [18.0, -1.5, 0.0],
                            "radial_velocity_mps": 0.0,
                            "material_tag": "asphalt",
                            "mesh_area_m2": 12.0,
                            "rcs_scale": 0.3,
                            "reflection_order": 2,
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        out_scene_json = root / "scene_from_asset.json"
        proc = subprocess.run(
            [
                "python3",
                "scripts/build_mesh_scene_from_asset_manifest.py",
                "--asset-manifest-json",
                str(asset_manifest),
                "--output-scene-json",
                str(out_scene_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Mesh scene build from asset manifest completed." in proc.stdout, proc.stdout

        scene = json.loads(out_scene_json.read_text(encoding="utf-8"))
        assert scene["backend"]["type"] == "mesh_material_stub"
        assert scene["scene_id"] == "asset_bridge_scene"
        assert len(scene["backend"]["objects"]) == 2
        assert len(scene["backend"]["materials"]) == 2
        assert scene["backend"]["objects"][0]["object_id"] == "car_a"
        assert scene["backend"]["objects"][0]["material_tag"] == "metal"
        assert scene["backend"]["objects"][0]["source_mesh_uri"] == "meshes/car_a.glb"

        out_dir = root / "outputs"
        run_out = run_object_scene_to_radar_map_json(
            scene_json_path=str(out_scene_json),
            output_dir=str(out_dir),
            run_hybrid_estimation=False,
        )
        assert (out_dir / "path_list.json").exists()
        assert (out_dir / "adc_cube.npz").exists()
        assert (out_dir / "radar_map.npz").exists()
        assert run_out["frame_count"] == 5

        path_payload = json.loads((out_dir / "path_list.json").read_text(encoding="utf-8"))
        assert len(path_payload) == 5
        assert len(path_payload[0]) == 2
        tags = {str(p["material_tag"]) for p in path_payload[0]}
        assert tags == {"metal", "asphalt"}

    print("validate_mesh_scene_import_bridge: pass")


if __name__ == "__main__":
    run()
