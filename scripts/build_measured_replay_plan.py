#!/usr/bin/env python3
import argparse

from avxsim.measured_pack_discovery import (
    build_measured_replay_plan_payload,
    discover_measured_replay_packs,
    save_measured_replay_plan_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Discover measured replay packs and build measured_replay_plan.json"
    )
    p.add_argument("--packs-root", required=True)
    p.add_argument("--output-plan-json", required=True)
    p.add_argument("--manifest-name", default="replay_manifest.json")
    p.add_argument("--lock-policy-name", default="lock_policy.json")
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--allow-empty", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    packs = discover_measured_replay_packs(
        packs_root=args.packs_root,
        manifest_name=args.manifest_name,
        lock_policy_name=args.lock_policy_name,
        recursive=bool(args.recursive),
    )
    if (len(packs) == 0) and (not args.allow_empty):
        raise ValueError("no replay packs discovered; use --allow-empty to write empty plan")

    payload = build_measured_replay_plan_payload(
        packs=packs,
        metadata={
            "packs_root": str(args.packs_root),
            "manifest_name": str(args.manifest_name),
            "lock_policy_name": str(args.lock_policy_name),
            "recursive": bool(args.recursive),
        },
    )
    save_measured_replay_plan_json(args.output_plan_json, payload)

    print("Measured replay plan build completed.")
    print(f"  packs_root: {args.packs_root}")
    print(f"  discovered_packs: {len(packs)}")
    print(f"  output: {args.output_plan_json}")


if __name__ == "__main__":
    main()
