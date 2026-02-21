import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


DEFAULT_PROFILE_LOCK_POLICY: Dict[str, Any] = {
    "min_pass_rate": 1.0,
    "max_case_fail_count": 0,
    "require_motion_defaults_enabled": False,
}


def load_replay_report_json(path: str) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("replay report must be JSON object")
    if "cases" not in payload or "summary" not in payload:
        raise ValueError("replay report missing summary/cases")
    if not isinstance(payload["cases"], list):
        raise ValueError("replay report cases must be list")
    if not isinstance(payload["summary"], dict):
        raise ValueError("replay report summary must be object")
    return payload


def build_profile_lock_report(
    replay_report: Mapping[str, Any],
    policy: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    p = _normalize_policy(policy)
    case_rows: List[Dict[str, Any]] = []

    for i, case in enumerate(replay_report.get("cases", [])):
        if not isinstance(case, Mapping):
            raise ValueError(f"replay report cases[{i}] must be object")

        scenario_id = str(case.get("scenario_id", f"scenario_{i+1}"))
        candidate_count = int(case.get("candidate_count", len(case.get("candidates", []))))
        pass_count = int(case.get("pass_count", 0))
        fail_count = int(case.get("fail_count", max(0, candidate_count - pass_count)))
        pass_rate = 0.0 if candidate_count == 0 else float(pass_count) / float(candidate_count)

        reasons: List[str] = []
        if pass_rate < float(p["min_pass_rate"]):
            reasons.append(
                f"pass_rate<{p['min_pass_rate']:.6f} ({pass_rate:.6f})"
            )
        if fail_count > int(p["max_case_fail_count"]):
            reasons.append(
                f"fail_count>{p['max_case_fail_count']} ({fail_count})"
            )

        motion_defaults = case.get("motion_compensation_defaults")
        motion_enabled = False
        if isinstance(motion_defaults, Mapping):
            motion_enabled = bool(motion_defaults.get("enabled", False))
        if bool(p["require_motion_defaults_enabled"]) and not motion_enabled:
            reasons.append("motion_compensation_defaults.enabled is False")

        case_rows.append(
            {
                "scenario_id": scenario_id,
                "profile_json": None
                if case.get("profile_json", None) is None
                else str(case.get("profile_json")),
                "reference_estimation_npz": str(case.get("reference_estimation_npz", "")),
                "candidate_count": candidate_count,
                "pass_count": pass_count,
                "fail_count": fail_count,
                "pass_rate": pass_rate,
                "motion_defaults_enabled": motion_enabled,
                "lock_pass": len(reasons) == 0,
                "lock_reasons": reasons,
            }
        )

    locked_count = sum(1 for c in case_rows if bool(c["lock_pass"]))
    unlocked_count = len(case_rows) - locked_count

    return {
        "version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "policy": p,
        "overall_lock_pass": unlocked_count == 0,
        "summary": {
            "case_count": int(len(case_rows)),
            "locked_count": int(locked_count),
            "unlocked_count": int(unlocked_count),
        },
        "cases": case_rows,
    }


def write_locked_profiles(
    replay_report: Mapping[str, Any],
    lock_report: Mapping[str, Any],
    output_dir: str,
    replay_report_json: Optional[str] = None,
) -> List[Dict[str, Any]]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    lock_by_scenario = {
        str(row["scenario_id"]): row
        for row in lock_report.get("cases", [])
        if isinstance(row, Mapping)
    }

    written: List[Dict[str, Any]] = []
    used_names = set()
    for i, case in enumerate(replay_report.get("cases", [])):
        if not isinstance(case, Mapping):
            continue
        profile_json = case.get("profile_json", None)
        if profile_json is None:
            continue

        scenario_id = str(case.get("scenario_id", f"scenario_{i+1}"))
        lock_case = lock_by_scenario.get(scenario_id, {})
        profile_payload = json.loads(Path(str(profile_json)).read_text(encoding="utf-8"))
        if not isinstance(profile_payload, dict):
            raise ValueError(f"profile_json for scenario '{scenario_id}' must be object")

        profile_payload["profile_lock"] = {
            "locked": bool(lock_case.get("lock_pass", False)),
            "locked_utc": datetime.now(timezone.utc).isoformat(),
            "policy": dict(lock_report.get("policy", {})),
            "replay_report_json": None if replay_report_json is None else str(replay_report_json),
            "replay_pass_count": int(lock_case.get("pass_count", 0)),
            "replay_fail_count": int(lock_case.get("fail_count", 0)),
            "replay_candidate_count": int(lock_case.get("candidate_count", 0)),
            "replay_pass_rate": float(lock_case.get("pass_rate", 0.0)),
            "lock_reasons": list(lock_case.get("lock_reasons", [])),
        }

        out_name = _unique_locked_name(
            scenario_id=scenario_id,
            index=i,
            used_names=used_names,
        )
        out_path = out_dir / out_name
        out_path.write_text(json.dumps(profile_payload, indent=2), encoding="utf-8")
        written.append(
            {
                "scenario_id": scenario_id,
                "input_profile_json": str(profile_json),
                "output_profile_json": str(out_path),
                "locked": bool(lock_case.get("lock_pass", False)),
            }
        )

    return written


def save_profile_lock_report_json(path: str, report: Mapping[str, Any]) -> None:
    Path(path).write_text(json.dumps(report, indent=2), encoding="utf-8")


def _normalize_policy(policy: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    out = dict(DEFAULT_PROFILE_LOCK_POLICY)
    if policy is not None:
        for key, value in policy.items():
            out[str(key)] = value

    out["min_pass_rate"] = float(out["min_pass_rate"])
    out["max_case_fail_count"] = int(out["max_case_fail_count"])
    out["require_motion_defaults_enabled"] = bool(out["require_motion_defaults_enabled"])

    if out["min_pass_rate"] < 0.0 or out["min_pass_rate"] > 1.0:
        raise ValueError("min_pass_rate must be in [0, 1]")
    if out["max_case_fail_count"] < 0:
        raise ValueError("max_case_fail_count must be >= 0")
    return out


def _unique_locked_name(scenario_id: str, index: int, used_names: set) -> str:
    base = _safe_name(scenario_id)
    if base == "":
        base = f"scenario_{index+1}"
    name = f"{base}.locked.json"
    if name not in used_names:
        used_names.add(name)
        return name
    suffix = 2
    while True:
        trial = f"{base}_{suffix}.locked.json"
        if trial not in used_names:
            used_names.add(trial)
            return trial
        suffix += 1


def _safe_name(text: str) -> str:
    chars = []
    for ch in str(text):
        if ch.isalnum() or ch in {"-", "_"}:
            chars.append(ch)
        else:
            chars.append("_")
    return "".join(chars).strip("_")
