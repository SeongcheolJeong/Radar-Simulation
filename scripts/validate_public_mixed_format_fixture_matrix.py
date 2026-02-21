#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def _run_case(
    repo_root: Path,
    env: dict,
    source_asset: Path,
    relative_path: str,
    scene_id: str,
    summary_json: Path,
) -> dict:
    proc = subprocess.run(
        [
            "python3",
            "scripts/run_public_scene_asset_onboarding.py",
            "--output-root",
            str(summary_json.parent / scene_id),
            "--asset-source-path",
            str(source_asset),
            "--asset-relative-path",
            relative_path,
            "--scene-id",
            scene_id,
            "--object-layout-preset",
            "single",
            "--strict",
            "--summary-json",
            str(summary_json),
        ],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Public scene-asset onboarding completed." in proc.stdout, proc.stdout
    return json.loads(summary_json.read_text(encoding="utf-8"))


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_public_mixed_format_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        source_glb = root / "fixture.glb"
        source_glb.write_bytes(b"glb fixture")

        source_obj = root / "fixture.obj"
        source_obj.write_text(
            "o fixture\n"
            "v 0.0 0.0 0.0\n"
            "v 1.0 0.0 0.0\n"
            "v 0.0 1.0 0.0\n"
            "f 1 2 3\n",
            encoding="utf-8",
        )

        glb_summary = _run_case(
            repo_root=repo_root,
            env=env,
            source_asset=source_glb,
            relative_path="assets/fixture.glb",
            scene_id="mixed_format_glb",
            summary_json=root / "summary_glb.json",
        )
        obj_summary = _run_case(
            repo_root=repo_root,
            env=env,
            source_asset=source_obj,
            relative_path="assets/fixture.obj",
            scene_id="mixed_format_obj",
            summary_json=root / "summary_obj.json",
        )

        glb_manifest = json.loads(
            Path(glb_summary["asset_manifest_json"]).read_text(encoding="utf-8")
        )
        obj_manifest = json.loads(
            Path(obj_summary["asset_manifest_json"]).read_text(encoding="utf-8")
        )
        assert glb_manifest["objects"][0]["source_mesh_format"] == "gltf"
        assert obj_manifest["objects"][0]["source_mesh_format"] == "obj"

        assert Path(glb_summary["run_result"]["path_list_json"]).exists()
        assert Path(glb_summary["run_result"]["adc_cube_npz"]).exists()
        assert Path(glb_summary["run_result"]["radar_map_npz"]).exists()
        assert Path(obj_summary["run_result"]["path_list_json"]).exists()
        assert Path(obj_summary["run_result"]["adc_cube_npz"]).exists()
        assert Path(obj_summary["run_result"]["radar_map_npz"]).exists()

    print("validate_public_mixed_format_fixture_matrix: pass")


if __name__ == "__main__":
    run()
