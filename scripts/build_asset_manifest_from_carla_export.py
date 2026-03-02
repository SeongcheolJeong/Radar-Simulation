#!/usr/bin/env python3
import argparse
from pathlib import Path
from typing import Optional, Sequence, Tuple

from avxsim.carla_export_bridge import (
    DEFAULT_CARLA_EXPORT_PROFILE,
    DEFAULT_CARLA_EXPORT_VERSION,
    build_asset_manifest_from_carla_export,
    load_carla_export_json,
)
from avxsim.scene_asset_parser import save_asset_manifest_json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Build normalized asset_manifest.json from CARLA scene export JSON "
            "(actors/sensor mount metadata)."
        )
    )
    p.add_argument("--carla-export-json", required=True)
    p.add_argument("--output-asset-manifest-json", required=True)
    p.add_argument("--default-material-tag", default="default_material")
    p.add_argument("--profile", default=DEFAULT_CARLA_EXPORT_PROFILE)
    p.add_argument("--expected-export-version", type=int, default=DEFAULT_CARLA_EXPORT_VERSION)

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

    p.add_argument(
        "--include-ego-actor",
        action="store_true",
        help="Keep ego actor in manifest objects (default excludes ego actor).",
    )
    p.add_argument(
        "--include-actor-types",
        default=None,
        help="Comma-separated actor_type allowlist (exact lower-case match).",
    )
    p.add_argument(
        "--exclude-actor-types",
        default=None,
        help="Comma-separated actor_type denylist (exact lower-case match).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    export_path = Path(args.carla_export_json).expanduser().resolve()
    out_json = Path(args.output_asset_manifest_json).expanduser().resolve()

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
    save_asset_manifest_json(str(out_json), manifest)

    parser_meta = manifest.get("asset_parser_metadata", {})
    print("Asset manifest build from CARLA export completed.")
    print(f"  carla_export_json: {export_path}")
    print(f"  output_asset_manifest_json: {out_json}")
    print(f"  scene_id: {manifest.get('scene_id')}")
    print(f"  object_count: {parser_meta.get('object_count')}")
    print(f"  excluded_actor_count: {parser_meta.get('excluded_actor_count')}")
    print(f"  dynamic_object_count: {parser_meta.get('dynamic_object_count')}")
    print(f"  static_object_count: {parser_meta.get('static_object_count')}")
    print(f"  schema_profile: {parser_meta.get('schema_profile')}")
    print(f"  schema_version: {parser_meta.get('schema_version')}")
    print(f"  strict_mode: {parser_meta.get('strict_mode')}")


def _parse_type_filter(value: Optional[str]) -> Optional[Tuple[str, ...]]:
    if value is None:
        return None
    tokens = [x.strip().lower() for x in str(value).split(",") if x.strip() != ""]
    if len(tokens) == 0:
        return None
    return tuple(tokens)


if __name__ == "__main__":
    main()
