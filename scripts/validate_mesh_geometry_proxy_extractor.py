#!/usr/bin/env python3
import json
import math
import os
import subprocess
import tempfile
from pathlib import Path

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def _assert_close_vec3(actual, expected, tol=1e-6):
    assert len(actual) == 3
    assert len(expected) == 3
    for a, e in zip(actual, expected):
        assert math.isclose(float(a), float(e), rel_tol=tol, abs_tol=tol), (actual, expected)


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_mesh_geometry_proxy_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        meshes = root / "meshes"
        meshes.mkdir(parents=True, exist_ok=True)

        obj_path = meshes / "tri.obj"
        obj_path.write_text(
            "o tri\n"
            "v 0.0 0.0 0.0\n"
            "v 2.0 0.0 0.0\n"
            "v 0.0 2.0 0.0\n"
            "f 1 2 3\n",
            encoding="utf-8",
        )

        gltf_path = meshes / "bbox_proxy.gltf"
        gltf_path.write_text(
            json.dumps(
                {
                    "asset": {"version": "2.0"},
                    "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
                    "accessors": [
                        {
                            "componentType": 5126,
                            "count": 3,
                            "type": "VEC3",
                            "min": [10.0, -1.0, 0.0],
                            "max": [14.0, 3.0, 2.0],
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        sidecar_json = root / "scene_sidecar.json"
        sidecar_json.write_text(
            json.dumps(
                {
                    "schema_profile": "v1",
                    "schema_version": 1,
                    "scene_id": "mesh_proxy_scene_v1",
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
                        "n_chirps": 4,
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
                        "metal": {"reflectivity": 0.9, "attenuation_db": 1.0},
                    },
                    "objects": [
                        {
                            "mesh_uri": "meshes/bbox_proxy.gltf",
                            "object_id": "gltf_auto",
                            "velocity_mps": [0.0, 0.0, 0.0],
                            "material_tag": "metal",
                            "rcs_scale": 1.0,
                        },
                        {
                            "mesh_uri": "meshes/tri.obj",
                            "object_id": "obj_auto",
                            "radial_velocity_mps": 0.0,
                            "material_tag": "metal",
                            "rcs_scale": 1.0,
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        asset_manifest_json = root / "asset_manifest.json"
        proc_manifest = subprocess.run(
            [
                "python3",
                "scripts/build_asset_manifest_from_sidecar.py",
                "--sidecar-json",
                str(sidecar_json),
                "--output-asset-manifest-json",
                str(asset_manifest_json),
                "--strict",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Asset manifest build from sidecar completed." in proc_manifest.stdout

        manifest = json.loads(asset_manifest_json.read_text(encoding="utf-8"))
        parser_meta = manifest["asset_parser_metadata"]
        assert parser_meta["auto_geometry_object_count"] == 2
        assert sorted(parser_meta["auto_geometry_object_ids"]) == ["gltf_auto", "obj_auto"]
        assert "centroid_m" in parser_meta["auto_geometry_fields"]["gltf_auto"]
        assert "mesh_area_m2" in parser_meta["auto_geometry_fields"]["gltf_auto"]
        assert "centroid_m" in parser_meta["auto_geometry_fields"]["obj_auto"]
        assert "mesh_area_m2" in parser_meta["auto_geometry_fields"]["obj_auto"]

        by_id = {item["object_id"]: item for item in manifest["objects"]}
        _assert_close_vec3(by_id["gltf_auto"]["centroid_m"], [12.0, 1.0, 1.0])
        assert math.isclose(float(by_id["gltf_auto"]["mesh_area_m2"]), 64.0, rel_tol=1e-6)
        _assert_close_vec3(by_id["obj_auto"]["centroid_m"], [1.0, 1.0, 0.0])
        assert math.isclose(float(by_id["obj_auto"]["mesh_area_m2"]), 2.0, rel_tol=1e-6)

        scene_json = root / "scene_from_manifest.json"
        proc_scene = subprocess.run(
            [
                "python3",
                "scripts/build_mesh_scene_from_asset_manifest.py",
                "--asset-manifest-json",
                str(asset_manifest_json),
                "--output-scene-json",
                str(scene_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Mesh scene build from asset manifest completed." in proc_scene.stdout

        out_dir = root / "outputs"
        out = run_object_scene_to_radar_map_json(
            scene_json_path=str(scene_json),
            output_dir=str(out_dir),
            run_hybrid_estimation=False,
        )
        assert out["frame_count"] == 4
        assert (out_dir / "path_list.json").exists()
        assert (out_dir / "adc_cube.npz").exists()
        assert (out_dir / "radar_map.npz").exists()

    print("validate_mesh_geometry_proxy_extractor: pass")


if __name__ == "__main__":
    run()
