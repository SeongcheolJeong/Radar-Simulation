#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path


def _run_onboarding(
    repo_root: Path,
    env: dict,
    source_asset: Path,
    output_root: Path,
    summary_json: Path,
) -> dict:
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
            "public_multi_object_fixture",
            "--object-layout-preset",
            "triple_lane",
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
    with tempfile.TemporaryDirectory(prefix="validate_public_multi_object_fixture_") as td:
        root = Path(td)
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        source_asset = root / "local_fixture.glb"
        source_asset.write_bytes(b"public multi-object fixture")

        output_root = root / "multi_object_onboarding"
        summary_1_json = root / "summary_1.json"
        summary_2_json = root / "summary_2.json"

        summary_1 = _run_onboarding(repo_root, env, source_asset, output_root, summary_1_json)
        summary_2 = _run_onboarding(repo_root, env, source_asset, output_root, summary_2_json)

        assert summary_1["object_layout_preset"] == "triple_lane"
        assert summary_1["run_result"]["frame_count"] == 8
        assert Path(summary_1["run_result"]["path_list_json"]).exists()
        assert Path(summary_1["run_result"]["adc_cube_npz"]).exists()
        assert Path(summary_1["run_result"]["radar_map_npz"]).exists()

        bundle_1 = json.loads(
            Path(summary_1["replay_bundle_manifest_json"]).read_text(encoding="utf-8")
        )
        bundle_2 = json.loads(
            Path(summary_2["replay_bundle_manifest_json"]).read_text(encoding="utf-8")
        )
        assert bundle_1["object_count"] == 3
        assert bundle_1["artifact_hashes"] == bundle_2["artifact_hashes"]

    print("validate_public_multi_object_fixture_bundle: pass")


if __name__ == "__main__":
    run()
