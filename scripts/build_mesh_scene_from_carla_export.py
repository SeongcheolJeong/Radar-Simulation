#!/usr/bin/env python3
import argparse
from pathlib import Path
from typing import Optional, Tuple

from avxsim.carla_export_bridge import (
    DEFAULT_CARLA_EXPORT_PROFILE,
    DEFAULT_CARLA_EXPORT_VERSION,
    build_asset_manifest_from_carla_export,
    load_carla_export_json,
)
from avxsim.scene_asset_bridge import (
    build_mesh_scene_payload_from_asset_manifest,
    save_scene_json,
)
from avxsim.scene_asset_parser import save_asset_manifest_json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Build object-scene JSON (mesh_material_stub backend) directly from "
            "CARLA export JSON by bridging through normalized asset_manifest."
        )
    )
    p.add_argument("--carla-export-json", required=True)
    p.add_argument("--output-scene-json", required=True)
    p.add_argument("--output-asset-manifest-json", default=None)

    p.add_argument("--default-material-tag", default="default_material")
    p.add_argument("--profile", default=DEFAULT_CARLA_EXPORT_PROFILE)
    p.add_argument("--expected-export-version", type=int, default=DEFAULT_CARLA_EXPORT_VERSION)

    strict_group = p.add_mutually_exclusive_group()
    strict_group.add_argument("--strict", dest="strict_mode", action="store_true")
    strict_group.add_argument("--non-strict", dest="strict_mode", action="store_false")
    p.set_defaults(strict_mode=True)

    p.add_argument("--include-ego-actor", action="store_true")
    p.add_argument("--include-actor-types", default=None)
    p.add_argument("--exclude-actor-types", default=None)

    p.add_argument("--scene-id", default=None)
    p.add_argument("--n-chirps", type=int, default=None)
    p.add_argument("--chirp-interval-s", type=float, default=None)
    p.add_argument("--fc-hz", type=float, default=None)
    p.add_argument("--slope-hz-per-s", type=float, default=None)
    p.add_argument("--fs-hz", type=float, default=None)
    p.add_argument("--samples-per-chirp", type=int, default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    export_path = Path(args.carla_export_json).expanduser().resolve()
    out_scene = Path(args.output_scene_json).expanduser().resolve()

    payload = load_carla_export_json(str(export_path))
    manifest = build_asset_manifest_from_carla_export(
        carla_payload=payload,
        default_material_tag=str(args.default_material_tag),
        profile=str(args.profile),
        expected_export_version=int(args.expected_export_version),
        strict_mode=bool(args.strict_mode),
        include_ego_actor=bool(args.include_ego_actor),
        include_actor_types=_parse_type_filter(args.include_actor_types),
        exclude_actor_types=_parse_type_filter(args.exclude_actor_types),
    )

    if args.output_asset_manifest_json is not None:
        out_manifest = Path(args.output_asset_manifest_json).expanduser().resolve()
        save_asset_manifest_json(str(out_manifest), manifest)
    else:
        out_manifest = None

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
    parser_meta = manifest.get("asset_parser_metadata", {})
    print("Mesh scene build from CARLA export completed.")
    print(f"  carla_export_json: {export_path}")
    if out_manifest is not None:
        print(f"  output_asset_manifest_json: {out_manifest}")
    print(f"  output_scene_json: {out_scene}")
    print(f"  scene_id: {scene['scene_id']}")
    print(f"  backend_type: {backend['type']}")
    print(f"  object_count: {len(backend['objects'])}")
    print(f"  excluded_actor_count: {parser_meta.get('excluded_actor_count')}")


def _parse_type_filter(value: Optional[str]) -> Optional[Tuple[str, ...]]:
    if value is None:
        return None
    tokens = [x.strip().lower() for x in str(value).split(",") if x.strip() != ""]
    if len(tokens) == 0:
        return None
    return tuple(tokens)


if __name__ == "__main__":
    main()
