#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_carla_export_bridge_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        export_json = root / "carla_export.json"
        export_json.write_text(json.dumps(_build_export_payload(), indent=2), encoding="utf-8")

        out_manifest = root / "asset_manifest_from_carla.json"
        out_scene = root / "scene_from_carla.json"

        proc = subprocess.run(
            [
                str(sys.executable),
                "scripts/build_mesh_scene_from_carla_export.py",
                "--carla-export-json",
                str(export_json),
                "--output-scene-json",
                str(out_scene),
                "--output-asset-manifest-json",
                str(out_manifest),
                "--strict",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Mesh scene build from CARLA export completed." in proc.stdout, proc.stdout

        manifest = json.loads(out_manifest.read_text(encoding="utf-8"))
        parser_meta = manifest["asset_parser_metadata"]
        assert parser_meta["source_type"] == "carla_export"
        assert parser_meta["actor_count"] == 4
        assert parser_meta["object_count"] == 2
        assert parser_meta["excluded_ego_actor_count"] == 1
        assert parser_meta["excluded_sensor_actor_count"] == 1
        assert parser_meta["auto_mesh_area_object_count"] >= 1
        assert len(manifest["objects"]) == 2
        for row in manifest["objects"]:
            assert "source_carla_actor_id" in row
            assert "source_carla_actor_type" in row
            assert float(row["mesh_area_m2"]) > 0.0

        scene = json.loads(out_scene.read_text(encoding="utf-8"))
        assert scene["backend"]["type"] == "mesh_material_stub"
        assert scene["scene_id"] == "carla_export_scene_v1"
        assert len(scene["backend"]["objects"]) == 2

        out_dir = root / "outputs"
        run_out = run_object_scene_to_radar_map_json(
            scene_json_path=str(out_scene),
            output_dir=str(out_dir),
            run_hybrid_estimation=False,
        )
        assert (out_dir / "path_list.json").exists()
        assert (out_dir / "adc_cube.npz").exists()
        assert (out_dir / "radar_map.npz").exists()
        assert run_out["frame_count"] == 6

        path_payload = json.loads((out_dir / "path_list.json").read_text(encoding="utf-8"))
        assert len(path_payload) == 6
        assert len(path_payload[0]) == 2
        for p in path_payload[0]:
            assert "path_id" in p
            assert "material_tag" in p
            assert "reflection_order" in p

    print("validate_carla_export_bridge: pass")


def _build_export_payload() -> dict:
    return {
        "schema_profile": "carla_export_v1",
        "schema_version": 1,
        "scene_id": "carla_export_scene_v1",
        "frame_id": 120,
        "timestamp_s": 3.2,
        "ego_actor_id": "100",
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
            "n_chirps": 6,
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
        "materials": {
            "vehicle_metal": {"reflectivity": 0.9, "attenuation_db": 1.0},
            "static_object": {"reflectivity": 0.35, "attenuation_db": 5.0},
        },
        "actors": [
            {
                "actor_id": "100",
                "actor_type": "vehicle.tesla.model3",
                "role_name": "hero",
                "location_m": [0.0, 0.0, 0.0],
                "velocity_mps": [0.0, 0.0, 0.0],
                "material_tag": "vehicle_metal",
                "bbox_extent_m": [2.3, 1.0, 0.8],
            },
            {
                "actor_id": "200",
                "actor_type": "vehicle.audi.tt",
                "location_m": [24.0, 1.4, 0.0],
                "velocity_mps": [-3.0, 0.0, 0.0],
                "material_tag": "vehicle_metal",
                "bbox_extent_m": [2.2, 0.9, 0.8],
            },
            {
                "actor_id": "300",
                "actor_type": "static.prop.trafficcone01",
                "location_m": [18.0, -1.2, 0.0],
                "radial_velocity_mps": 0.0,
                "material_tag": "static_object",
                "bbox_extent_m": [0.2, 0.2, 0.5],
                "rcs_scale": 0.4,
                "reflection_order": 2,
            },
            {
                "actor_id": "900",
                "actor_type": "sensor.camera.rgb",
                "location_m": [0.0, 0.0, 1.7],
                "velocity_mps": [0.0, 0.0, 0.0],
            },
        ],
    }


if __name__ == "__main__":
    run()
