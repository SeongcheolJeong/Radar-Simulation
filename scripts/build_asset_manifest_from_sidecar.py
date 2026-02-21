#!/usr/bin/env python3
import argparse
from pathlib import Path

from avxsim.scene_asset_parser import (
    DEFAULT_SIDECAR_PROFILE,
    DEFAULT_SIDECAR_VERSION,
    build_asset_manifest_from_sidecar,
    load_scene_sidecar_json,
    save_asset_manifest_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Build normalized asset_manifest.json from scene sidecar metadata "
            "(glTF/OBJ mesh references)."
        )
    )
    p.add_argument("--sidecar-json", required=True)
    p.add_argument("--output-asset-manifest-json", required=True)
    p.add_argument("--mesh-root", default=None)
    p.add_argument("--allow-missing-meshes", action="store_true")
    p.add_argument("--default-material-tag", default="default_material")
    p.add_argument("--profile", default=DEFAULT_SIDECAR_PROFILE)
    p.add_argument("--expected-sidecar-version", type=int, default=DEFAULT_SIDECAR_VERSION)
    strict_group = p.add_mutually_exclusive_group()
    strict_group.add_argument(
        "--strict",
        dest="strict_mode",
        action="store_true",
        help="Enable strict schema gate (default).",
    )
    strict_group.add_argument(
        "--non-strict",
        dest="strict_mode",
        action="store_false",
        help="Disable strict schema gate for exploratory ingestion.",
    )
    p.set_defaults(strict_mode=True)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    sidecar_path = Path(args.sidecar_json).expanduser().resolve()
    out_json = Path(args.output_asset_manifest_json).expanduser().resolve()
    strict_mode = bool(args.strict_mode)

    sidecar = load_scene_sidecar_json(str(sidecar_path))
    manifest = build_asset_manifest_from_sidecar(
        sidecar_payload=sidecar,
        sidecar_json_path=str(sidecar_path),
        mesh_root=args.mesh_root,
        allow_missing_meshes=bool(args.allow_missing_meshes),
        default_material_tag=str(args.default_material_tag),
        profile=str(args.profile),
        expected_sidecar_version=int(args.expected_sidecar_version),
        strict_mode=bool(strict_mode),
    )
    save_asset_manifest_json(str(out_json), manifest)

    parser_meta = manifest.get("asset_parser_metadata", {})
    print("Asset manifest build from sidecar completed.")
    print(f"  sidecar_json: {sidecar_path}")
    print(f"  output_asset_manifest_json: {out_json}")
    print(f"  scene_id: {manifest.get('scene_id')}")
    print(f"  object_count: {parser_meta.get('object_count')}")
    print(f"  mesh_format_counts: {parser_meta.get('mesh_format_counts')}")
    print(f"  schema_profile: {parser_meta.get('schema_profile')}")
    print(f"  schema_version: {parser_meta.get('schema_version')}")
    print(f"  strict_mode: {parser_meta.get('strict_mode')}")


if __name__ == "__main__":
    main()
