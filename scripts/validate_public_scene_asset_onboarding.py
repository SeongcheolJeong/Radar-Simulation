#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def run() -> None:
    with tempfile.TemporaryDirectory(prefix="validate_public_scene_onboarding_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        source_asset = root / "local_fixture.glb"
        source_asset.write_bytes(b"local glb fixture")

        output_root = root / "onboarding_run"
        summary_json = root / "onboarding_summary.json"
        proc = subprocess.run(
            [
                "python3",
                "scripts/run_public_scene_asset_onboarding.py",
                "--output-root",
                str(output_root),
                "--asset-source-path",
                str(source_asset),
                "--asset-relative-path",
                "assets/fixture.glb",
                "--scene-id",
                "public_scene_fixture_validation",
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

        summary = json.loads(summary_json.read_text(encoding="utf-8"))
        assert summary["scene_id"] == "public_scene_fixture_validation"
        assert summary["strict_mode"] is True
        assert summary["asset_source"].startswith("source_path:")
        assert summary["object_layout_preset"] == "single"
        bundle_manifest_json = Path(summary["replay_bundle_manifest_json"])
        assert bundle_manifest_json.exists()
        bundle = json.loads(bundle_manifest_json.read_text(encoding="utf-8"))
        assert bundle["object_count"] == 1
        assert bundle["artifact_hashes"]["path_list_json_sha256"]
        assert bundle["artifact_hashes"]["adc_cube_npz_sha256"]
        assert bundle["artifact_hashes"]["radar_map_npz_sha256"]

        run_result = summary["run_result"]
        assert Path(run_result["path_list_json"]).exists()
        assert Path(run_result["adc_cube_npz"]).exists()
        assert Path(run_result["radar_map_npz"]).exists()
        assert int(run_result["frame_count"]) == 8

    print("validate_public_scene_asset_onboarding: pass")


if __name__ == "__main__":
    run()
