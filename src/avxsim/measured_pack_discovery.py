import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


def discover_measured_replay_packs(
    packs_root: str,
    manifest_name: str = "replay_manifest.json",
    lock_policy_name: str = "lock_policy.json",
    recursive: bool = False,
) -> List[Dict[str, Any]]:
    root = Path(packs_root)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"packs_root must be existing directory: {packs_root}")

    if recursive:
        manifest_paths = sorted(root.rglob(manifest_name))
    else:
        manifest_paths = sorted(root.glob(f"*/{manifest_name}"))

    packs: List[Dict[str, Any]] = []
    for manifest in manifest_paths:
        pack_dir = manifest.parent
        pack_id = pack_dir.name

        row: Dict[str, Any] = {
            "pack_id": pack_id,
            "replay_manifest_json": str(manifest),
            "output_subdir": pack_id,
        }

        lock_policy_json = pack_dir / lock_policy_name
        if lock_policy_json.exists():
            policy = json.loads(lock_policy_json.read_text(encoding="utf-8"))
            if not isinstance(policy, Mapping):
                raise ValueError(f"lock policy must be object: {lock_policy_json}")
            row["lock_policy"] = dict(policy)

        packs.append(row)

    return packs


def build_measured_replay_plan_payload(
    packs: Sequence[Mapping[str, Any]],
    metadata: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "version": 1,
        "packs": [dict(p) for p in packs],
    }
    if metadata is not None:
        payload["metadata"] = dict(metadata)
    return payload


def save_measured_replay_plan_json(path: str, payload: Mapping[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
