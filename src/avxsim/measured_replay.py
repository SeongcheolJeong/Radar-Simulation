import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .profile_lock import build_profile_lock_report, write_locked_profiles
from .replay_batch import run_replay_manifest, save_replay_report_json


DEFAULT_MEASURED_REPLAY_LOCK_POLICY: Dict[str, Any] = {
    "min_pass_rate": 1.0,
    "max_case_fail_count": 0,
    "require_motion_defaults_enabled": False,
}


def load_measured_replay_plan_json(path: str) -> List[Dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        packs = payload.get("packs", None)
    else:
        packs = payload
    if not isinstance(packs, list) or len(packs) == 0:
        raise ValueError("measured replay plan must contain non-empty packs list")

    out: List[Dict[str, Any]] = []
    for i, pack in enumerate(packs):
        if not isinstance(pack, dict):
            raise ValueError(f"packs[{i}] must be object")
        if "replay_manifest_json" not in pack:
            raise ValueError(f"packs[{i}] missing replay_manifest_json")

        lock_policy = pack.get("lock_policy", None)
        if lock_policy is not None and not isinstance(lock_policy, dict):
            raise ValueError(f"packs[{i}].lock_policy must be object")

        out.append(
            {
                "pack_id": str(pack.get("pack_id", f"pack_{i+1}")),
                "replay_manifest_json": str(pack["replay_manifest_json"]),
                "output_subdir": None
                if pack.get("output_subdir", None) is None
                else str(pack["output_subdir"]),
                "lock_policy": None if lock_policy is None else dict(lock_policy),
            }
        )
    return out


def run_measured_replay_plan(
    packs: Sequence[Mapping[str, Any]],
    output_root: str,
    default_lock_policy: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)

    default_policy = dict(DEFAULT_MEASURED_REPLAY_LOCK_POLICY)
    if default_lock_policy is not None:
        for key, value in default_lock_policy.items():
            default_policy[str(key)] = value

    pack_reports: List[Dict[str, Any]] = []
    total_case_count = 0
    total_locked_count = 0
    total_unlocked_count = 0

    for i, pack in enumerate(packs):
        pack_id = str(pack.get("pack_id", f"pack_{i+1}"))
        subdir = pack.get("output_subdir", None)
        if subdir is None:
            out_dir = root / _safe_name(pack_id)
        else:
            out_dir = root / str(subdir)
        out_dir.mkdir(parents=True, exist_ok=True)

        replay_report = run_replay_manifest(str(pack["replay_manifest_json"]))
        replay_report_json = out_dir / "replay_report.json"
        save_replay_report_json(str(replay_report_json), replay_report)

        merged_policy = dict(default_policy)
        if pack.get("lock_policy", None) is not None:
            for key, value in dict(pack["lock_policy"]).items():
                merged_policy[str(key)] = value

        lock_report = build_profile_lock_report(
            replay_report=replay_report,
            policy=merged_policy,
        )
        written = write_locked_profiles(
            replay_report=replay_report,
            lock_report=lock_report,
            output_dir=str(out_dir / "locked_profiles"),
            replay_report_json=str(replay_report_json),
        )
        lock_report["locked_profiles"] = written

        lock_report_json = out_dir / "profile_lock_report.json"
        lock_report_json.write_text(json.dumps(lock_report, indent=2), encoding="utf-8")

        summary = lock_report["summary"]
        case_count = int(summary.get("case_count", 0))
        locked_count = int(summary.get("locked_count", 0))
        unlocked_count = int(summary.get("unlocked_count", 0))

        total_case_count += case_count
        total_locked_count += locked_count
        total_unlocked_count += unlocked_count

        pack_reports.append(
            {
                "pack_id": pack_id,
                "replay_manifest_json": str(pack["replay_manifest_json"]),
                "output_dir": str(out_dir),
                "replay_report_json": str(replay_report_json),
                "profile_lock_report_json": str(lock_report_json),
                "overall_lock_pass": bool(lock_report.get("overall_lock_pass", False)),
                "summary": {
                    "case_count": case_count,
                    "locked_count": locked_count,
                    "unlocked_count": unlocked_count,
                },
            }
        )

    overall_pass = total_unlocked_count == 0
    return {
        "version": 1,
        "output_root": str(root),
        "overall_lock_pass": overall_pass,
        "summary": {
            "pack_count": int(len(pack_reports)),
            "case_count": int(total_case_count),
            "locked_count": int(total_locked_count),
            "unlocked_count": int(total_unlocked_count),
        },
        "packs": pack_reports,
    }


def run_measured_replay_plan_json(
    plan_json: str,
    output_root: str,
    default_lock_policy: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    packs = load_measured_replay_plan_json(plan_json)
    return run_measured_replay_plan(
        packs=packs,
        output_root=output_root,
        default_lock_policy=default_lock_policy,
    )


def save_measured_replay_summary_json(path: str, summary: Mapping[str, Any]) -> None:
    Path(path).write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _safe_name(text: str) -> str:
    chars = []
    for ch in str(text):
        if ch.isalnum() or ch in {"-", "_"}:
            chars.append(ch)
        else:
            chars.append("_")
    name = "".join(chars).strip("_")
    return name if name != "" else "pack"
