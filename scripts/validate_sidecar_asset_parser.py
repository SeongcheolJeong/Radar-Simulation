#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_sidecar_parser_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        meshes = root / "meshes"
        meshes.mkdir(parents=True, exist_ok=True)
        (meshes / "car_a.glb").write_bytes(b"stub")
        (meshes / "cone_b.obj").write_text("# stub obj\n", encoding="utf-8")

        sidecar_json = root / "scene_sidecar.json"
        sidecar_json.write_text(
            json.dumps(
                {
                    "schema_profile": "v1",
                    "schema_version": 1,
                    "scene_id": "sidecar_scene_v1",
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
                        "plastic": {"reflectivity": 0.3, "attenuation_db": 6.0},
                    },
                    "objects": [
                        {
                            "mesh_uri": "meshes/car_a.glb",
                            "id": "car_a",
                            "bbox_center_m": [24.0, 0.5, 0.0],
                            "velocity_mps": [2.0, 0.0, 0.0],
                            "material": "metal",
                            "mesh_area": 7.0,
                            "rcs_scale": 1.0,
                        },
                        {
                            "mesh_file": "meshes/cone_b.obj",
                            "object_id": "cone_b",
                            "centroid_m": [18.0, -1.2, 0.0],
                            "radial_velocity_mps": 0.0,
                            "material_tag": "plastic",
                            "mesh_area_m2": 0.8,
                            "rcs_scale": 0.4,
                            "reflection_order": 2,
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
        assert "Asset manifest build from sidecar completed." in proc_manifest.stdout, proc_manifest.stdout

        manifest = json.loads(asset_manifest_json.read_text(encoding="utf-8"))
        parser_meta = manifest["asset_parser_metadata"]
        assert parser_meta["mesh_format_counts"]["gltf"] == 1
        assert parser_meta["mesh_format_counts"]["obj"] == 1
        assert parser_meta["schema_profile"] == "v1"
        assert parser_meta["schema_version"] == 1
        assert parser_meta["strict_mode"] is True
        assert len(manifest["objects"]) == 2
        assert manifest["objects"][0]["source_mesh_format"] == "gltf"
        assert manifest["objects"][1]["source_mesh_format"] == "obj"

        # strict mode rejects unknown top-level keys.
        bad_sidecar = root / "scene_sidecar_bad.json"
        bad_payload = json.loads(sidecar_json.read_text(encoding="utf-8"))
        bad_payload["unexpected_field"] = 123
        bad_sidecar.write_text(json.dumps(bad_payload, indent=2), encoding="utf-8")
        proc_bad = subprocess.run(
            [
                "python3",
                "scripts/build_asset_manifest_from_sidecar.py",
                "--sidecar-json",
                str(bad_sidecar),
                "--output-asset-manifest-json",
                str(root / "bad_asset_manifest.json"),
                "--strict",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc_bad.returncode != 0

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
        assert "Mesh scene build from asset manifest completed." in proc_scene.stdout, proc_scene.stdout

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

    print("validate_sidecar_asset_parser: pass")


if __name__ == "__main__":
    run()
