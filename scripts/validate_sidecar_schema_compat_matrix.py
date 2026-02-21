#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path

from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_sidecar_schema_matrix_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        meshes = root / "meshes"
        meshes.mkdir(parents=True, exist_ok=True)
        (meshes / "car_a.glb").write_bytes(b"stub")

        sidecar_payload = {
            "schema_profile": "v1",
            "schema_version": 1,
            "scene_id": "schema_matrix_scene_v1",
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
                    "mesh_uri": "meshes/car_a.glb",
                    "object_id": "car_a",
                    "centroid_m": [20.0, 0.2, 0.0],
                    "velocity_mps": [1.0, 0.0, 0.0],
                    "material_tag": "metal",
                    "mesh_area_m2": 7.0,
                    "rcs_scale": 1.0,
                    "experimental_rcs_hint": 0.37,
                }
            ],
            "unexpected_top_level": {"mode": "candidate"},
        }
        sidecar_json = root / "scene_sidecar_candidate.json"
        sidecar_json.write_text(json.dumps(sidecar_payload, indent=2), encoding="utf-8")

        strict_manifest_json = root / "asset_manifest_strict.json"
        strict_proc = subprocess.run(
            [
                "python3",
                "scripts/build_asset_manifest_from_sidecar.py",
                "--sidecar-json",
                str(sidecar_json),
                "--output-asset-manifest-json",
                str(strict_manifest_json),
                "--strict",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert strict_proc.returncode != 0
        assert "unknown top-level keys in strict mode" in (strict_proc.stderr + strict_proc.stdout)

        non_strict_manifest_json = root / "asset_manifest_non_strict.json"
        non_strict_proc = subprocess.run(
            [
                "python3",
                "scripts/build_asset_manifest_from_sidecar.py",
                "--sidecar-json",
                str(sidecar_json),
                "--output-asset-manifest-json",
                str(non_strict_manifest_json),
                "--non-strict",
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert (
            "Asset manifest build from sidecar completed." in non_strict_proc.stdout
        ), non_strict_proc.stdout

        non_strict_manifest = json.loads(non_strict_manifest_json.read_text(encoding="utf-8"))
        parser_meta = non_strict_manifest["asset_parser_metadata"]
        assert parser_meta["strict_mode"] is False
        assert parser_meta["schema_profile"] == "v1"
        assert parser_meta["schema_version"] == 1
        assert "unexpected_top_level" in parser_meta["unknown_top_level_keys"]
        assert "0" in parser_meta["unknown_object_keys"]
        assert "experimental_rcs_hint" in parser_meta["unknown_object_keys"]["0"]

        scene_json = root / "scene_from_non_strict_manifest.json"
        build_scene_proc = subprocess.run(
            [
                "python3",
                "scripts/build_mesh_scene_from_asset_manifest.py",
                "--asset-manifest-json",
                str(non_strict_manifest_json),
                "--output-scene-json",
                str(scene_json),
            ],
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert (
            "Mesh scene build from asset manifest completed." in build_scene_proc.stdout
        ), build_scene_proc.stdout

        output_dir = root / "scene_outputs"
        out = run_object_scene_to_radar_map_json(
            scene_json_path=str(scene_json),
            output_dir=str(output_dir),
            run_hybrid_estimation=False,
        )
        assert out["frame_count"] == 4
        assert (output_dir / "path_list.json").exists()
        assert (output_dir / "adc_cube.npz").exists()
        assert (output_dir / "radar_map.npz").exists()

    print("validate_sidecar_schema_compat_matrix: pass")


if __name__ == "__main__":
    run()
