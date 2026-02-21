#!/usr/bin/env python3
import argparse
from pathlib import Path

from avxsim.scene_asset_bridge import (
    build_mesh_scene_payload_from_asset_manifest,
    load_scene_asset_manifest_json,
    save_scene_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Build object-scene JSON (mesh_material_stub backend) from external "
            "scene asset manifest JSON."
        )
    )
    p.add_argument("--asset-manifest-json", required=True)
    p.add_argument("--output-scene-json", required=True)
    p.add_argument("--scene-id", default=None)
    p.add_argument("--n-chirps", type=int, default=None)
    p.add_argument("--chirp-interval-s", type=float, default=None)
    p.add_argument("--fc-hz", type=float, default=None)
    p.add_argument("--slope-hz-per-s", type=float, default=None)
    p.add_argument("--fs-hz", type=float, default=None)
    p.add_argument("--samples-per-chirp", type=int, default=None)
    p.add_argument("--default-material-tag", default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.asset_manifest_json).expanduser().resolve()
    out_scene = Path(args.output_scene_json).expanduser().resolve()

    manifest = load_scene_asset_manifest_json(str(manifest_path))
    scene = build_mesh_scene_payload_from_asset_manifest(
        asset_manifest=manifest,
        scene_id=args.scene_id,
        n_chirps=args.n_chirps,
        chirp_interval_s=args.chirp_interval_s,
        fc_hz=args.fc_hz,
        slope_hz_per_s=args.slope_hz_per_s,
        fs_hz=args.fs_hz,
        samples_per_chirp=args.samples_per_chirp,
        default_material_tag=args.default_material_tag,
    )
    save_scene_json(str(out_scene), scene)

    backend = scene["backend"]
    print("Mesh scene build from asset manifest completed.")
    print(f"  asset_manifest_json: {manifest_path}")
    print(f"  output_scene_json: {out_scene}")
    print(f"  scene_id: {scene['scene_id']}")
    print(f"  backend_type: {backend['type']}")
    print(f"  object_count: {len(backend['objects'])}")
    print(f"  material_count: {len(backend['materials'])}")


if __name__ == "__main__":
    main()
