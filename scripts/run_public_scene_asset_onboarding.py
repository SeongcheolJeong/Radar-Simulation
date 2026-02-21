#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path
from typing import Any, Dict

from avxsim.scene_asset_bridge import build_mesh_scene_payload_from_asset_manifest, save_scene_json
from avxsim.scene_asset_parser import (
    DEFAULT_SIDECAR_PROFILE,
    DEFAULT_SIDECAR_VERSION,
    build_asset_manifest_from_sidecar,
    save_asset_manifest_json,
)
from avxsim.scene_pipeline import run_object_scene_to_radar_map_json


DEFAULT_BOX_GLB_URL = (
    "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/"
    "Models/Box/glTF-Binary/Box.glb"
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Onboard a public scene asset (glTF/OBJ), build sidecar/manifest/scene, "
            "and run object-scene radar pipeline."
        )
    )
    p.add_argument("--output-root", required=True)
    p.add_argument("--asset-url", default=DEFAULT_BOX_GLB_URL)
    p.add_argument("--asset-source-path", default=None)
    p.add_argument("--asset-relative-path", default="assets/public_asset.glb")
    p.add_argument("--scene-id", default="public_scene_asset_v1")
    p.add_argument("--force-refresh-asset", action="store_true")
    p.add_argument("--profile", default=DEFAULT_SIDECAR_PROFILE)
    p.add_argument("--expected-sidecar-version", type=int, default=DEFAULT_SIDECAR_VERSION)

    strict_group = p.add_mutually_exclusive_group()
    strict_group.add_argument("--strict", dest="strict_mode", action="store_true")
    strict_group.add_argument("--non-strict", dest="strict_mode", action="store_false")
    p.set_defaults(strict_mode=True)

    p.add_argument("--summary-json", default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    output_root = Path(args.output_root).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    asset_path = (output_root / args.asset_relative_path).resolve()
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    source = _materialize_asset(
        asset_path=asset_path,
        asset_source_path=args.asset_source_path,
        asset_url=args.asset_url,
        force_refresh=bool(args.force_refresh_asset),
    )

    sidecar_payload = _build_default_sidecar_payload(
        scene_id=str(args.scene_id),
        mesh_uri=args.asset_relative_path,
        object_id=asset_path.stem,
    )
    sidecar_json = output_root / "scene_sidecar_public_asset.json"
    sidecar_json.write_text(json.dumps(sidecar_payload, indent=2), encoding="utf-8")

    asset_manifest = build_asset_manifest_from_sidecar(
        sidecar_payload=sidecar_payload,
        sidecar_json_path=str(sidecar_json),
        mesh_root=None,
        allow_missing_meshes=False,
        default_material_tag="default_material",
        profile=str(args.profile),
        expected_sidecar_version=int(args.expected_sidecar_version),
        strict_mode=bool(args.strict_mode),
    )
    asset_manifest_json = output_root / "asset_manifest.json"
    save_asset_manifest_json(str(asset_manifest_json), asset_manifest)

    scene_payload = build_mesh_scene_payload_from_asset_manifest(asset_manifest=asset_manifest)
    scene_json = output_root / "scene.json"
    save_scene_json(str(scene_json), scene_payload)

    outputs_root = output_root / "scene_outputs"
    run_result = run_object_scene_to_radar_map_json(
        scene_json_path=str(scene_json),
        output_dir=str(outputs_root),
        run_hybrid_estimation=False,
    )

    summary_json = (
        Path(args.summary_json).expanduser().resolve()
        if args.summary_json is not None
        else output_root / "onboarding_summary.json"
    )
    summary_payload: Dict[str, Any] = {
        "scene_id": str(args.scene_id),
        "profile": str(args.profile),
        "expected_sidecar_version": int(args.expected_sidecar_version),
        "strict_mode": bool(args.strict_mode),
        "asset_source": source,
        "asset_relative_path": args.asset_relative_path,
        "asset_sha256": _sha256_hex(asset_path),
        "sidecar_json": str(sidecar_json),
        "asset_manifest_json": str(asset_manifest_json),
        "scene_json": str(scene_json),
        "run_result": run_result,
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    print("Public scene-asset onboarding completed.")
    print(f"  output_root: {output_root}")
    print(f"  asset_source: {source}")
    print(f"  asset_path: {asset_path}")
    print(f"  summary_json: {summary_json}")
    print(f"  radar_map_npz: {run_result['radar_map_npz']}")


def _materialize_asset(
    asset_path: Path,
    asset_source_path: str,
    asset_url: str,
    force_refresh: bool,
) -> str:
    if asset_source_path is not None:
        src = Path(asset_source_path).expanduser().resolve()
        if not src.exists() or not src.is_file():
            raise FileNotFoundError(f"asset source path not found: {src}")
        if force_refresh or not asset_path.exists():
            shutil.copyfile(str(src), str(asset_path))
        return f"source_path:{src}"

    if asset_url is None or str(asset_url).strip() == "":
        raise ValueError("asset-url is required when asset-source-path is not provided")
    if asset_path.exists() and asset_path.is_file() and not force_refresh:
        return f"cached_url:{asset_url}"

    urllib.request.urlretrieve(str(asset_url), str(asset_path))
    return f"url:{asset_url}"


def _build_default_sidecar_payload(scene_id: str, mesh_uri: str, object_id: str) -> Dict[str, Any]:
    return {
        "schema_profile": DEFAULT_SIDECAR_PROFILE,
        "schema_version": DEFAULT_SIDECAR_VERSION,
        "scene_id": scene_id,
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
            "n_chirps": 8,
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
            "default_material": {
                "reflectivity": 0.8,
                "attenuation_db": 2.0,
            }
        },
        "objects": [
            {
                "mesh_uri": mesh_uri,
                "object_id": object_id,
                "centroid_m": [20.0, 0.0, 0.0],
                "velocity_mps": [0.0, 0.0, 0.0],
                "material_tag": "default_material",
                "mesh_area_m2": 1.0,
                "rcs_scale": 1.0,
            }
        ],
    }


def _sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    main()
