#!/usr/bin/env python3
import argparse

from avxsim.replay_manifest_builder import (
    DEFAULT_CANDIDATE_GLOBS,
    build_replay_manifest_case,
    build_replay_manifest_payload,
    discover_candidate_npz_paths,
    resolve_profile_json,
    save_replay_manifest_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build replay_manifest.json from measured pack folder"
    )
    p.add_argument("--pack-root", required=True)
    p.add_argument("--scenario-id", default=None)
    p.add_argument("--profile-json", default=None)
    p.add_argument("--reference-estimation-npz", default=None)
    p.add_argument(
        "--candidate-glob",
        action="append",
        default=[],
        help="Glob relative to pack root (repeatable)",
    )
    p.add_argument(
        "--exclude-glob",
        action="append",
        default=[],
        help="Exclude glob relative to pack root (repeatable)",
    )
    p.add_argument(
        "--candidate-name-mode",
        choices=["stem", "name", "relative"],
        default="stem",
    )
    p.add_argument(
        "--include-sidecar-metadata",
        action="store_true",
        help="Load candidate sidecar metadata from .json or .meta.json",
    )
    p.add_argument(
        "--allow-empty-candidates",
        action="store_true",
        help="Allow writing manifest with zero candidates",
    )
    p.add_argument(
        "--output-manifest-json",
        default=None,
        help="Default: <pack-root>/replay_manifest.json",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    candidate_globs = args.candidate_glob if len(args.candidate_glob) > 0 else list(DEFAULT_CANDIDATE_GLOBS)
    profile_json = resolve_profile_json(args.pack_root, profile_json=args.profile_json)

    candidate_paths = discover_candidate_npz_paths(
        pack_root=args.pack_root,
        candidate_globs=candidate_globs,
        exclude_globs=args.exclude_glob,
    )
    if (len(candidate_paths) == 0) and (not args.allow_empty_candidates):
        raise ValueError("no candidate npz discovered; use --allow-empty-candidates to override")

    case = build_replay_manifest_case(
        pack_root=args.pack_root,
        scenario_id=args.scenario_id,
        profile_json=str(profile_json),
        candidate_paths=[str(p) for p in candidate_paths],
        reference_estimation_npz=args.reference_estimation_npz,
        include_sidecar_metadata=bool(args.include_sidecar_metadata),
        candidate_name_mode=str(args.candidate_name_mode),
    )
    payload = build_replay_manifest_payload([case])

    out_json = args.output_manifest_json
    if out_json is None:
        out_json = str((profile_json.parent / "replay_manifest.json"))
    save_replay_manifest_json(out_json, payload)

    print("Replay manifest build completed.")
    print(f"  pack_root: {args.pack_root}")
    print(f"  scenario_id: {case['scenario_id']}")
    print(f"  candidates: {len(case['candidates'])}")
    print(f"  output: {out_json}")


if __name__ == "__main__":
    main()
