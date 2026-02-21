import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .parity import compare_hybrid_estimation_npz
from .scenario_profile import load_scenario_profile_json


def load_replay_manifest_json(path: str) -> List[Dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        cases = payload.get("cases", None)
    else:
        cases = payload
    if not isinstance(cases, list) or len(cases) == 0:
        raise ValueError("replay manifest must contain non-empty cases list")

    out: List[Dict[str, Any]] = []
    for i, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{i}] must be object")
        if "candidates" not in case:
            raise ValueError(f"cases[{i}] missing candidates")
        cands = case["candidates"]
        if not isinstance(cands, list) or len(cands) == 0:
            raise ValueError(f"cases[{i}].candidates must be non-empty list")

        parsed_cands = []
        for j, cand in enumerate(cands):
            if not isinstance(cand, dict):
                raise ValueError(f"cases[{i}].candidates[{j}] must be object")
            if "estimation_npz" not in cand:
                raise ValueError(f"cases[{i}].candidates[{j}] missing estimation_npz")
            parsed_cands.append(
                {
                    "name": str(cand.get("name", f"candidate_{j+1}")),
                    "estimation_npz": str(cand["estimation_npz"]),
                    "metadata": dict(cand.get("metadata", {})),
                }
            )

        thresholds = case.get("parity_thresholds", None)
        if thresholds is not None:
            if not isinstance(thresholds, dict):
                raise ValueError(f"cases[{i}].parity_thresholds must be object")
            thresholds = {str(k): float(v) for k, v in thresholds.items()}

        out.append(
            {
                "scenario_id": str(case.get("scenario_id", f"scenario_{i+1}")),
                "profile_json": None if case.get("profile_json", None) is None else str(case["profile_json"]),
                "reference_estimation_npz": None
                if case.get("reference_estimation_npz", None) is None
                else str(case["reference_estimation_npz"]),
                "parity_thresholds": thresholds,
                "candidates": parsed_cands,
            }
        )
    return out


def run_replay_cases(
    cases: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    case_reports: List[Dict[str, Any]] = []
    total_candidates = 0
    total_pass = 0
    total_fail = 0

    for i, case in enumerate(cases):
        scenario_id = str(case.get("scenario_id", f"scenario_{i+1}"))
        profile_json = case.get("profile_json", None)
        thresholds = case.get("parity_thresholds", None)
        reference = case.get("reference_estimation_npz", None)
        profile = None
        if profile_json is not None:
            profile = load_scenario_profile_json(str(profile_json))
            if thresholds is None:
                thresholds = dict(profile["parity_thresholds"])
            if reference is None:
                reference = profile.get("reference_estimation_npz", None)
        if reference is None:
            raise ValueError(f"case '{scenario_id}' missing reference_estimation_npz")
        if thresholds is None:
            raise ValueError(f"case '{scenario_id}' missing parity_thresholds/profile")

        cand_reports = []
        pass_count = 0
        fail_count = 0
        for cand in case["candidates"]:
            total_candidates += 1
            rep = compare_hybrid_estimation_npz(
                reference_npz=str(reference),
                candidate_npz=str(cand["estimation_npz"]),
                thresholds=thresholds,
            )
            ok = bool(rep["pass"])
            if ok:
                pass_count += 1
                total_pass += 1
            else:
                fail_count += 1
                total_fail += 1
            cand_reports.append(
                {
                    "name": str(cand.get("name", "")),
                    "estimation_npz": str(cand["estimation_npz"]),
                    "pass": ok,
                    "failure_count": len(rep["failures"]),
                    "failures": rep["failures"],
                    "metrics": rep["metrics"],
                    "metadata": dict(cand.get("metadata", {})),
                }
            )

        case_reports.append(
            {
                "scenario_id": scenario_id,
                "reference_estimation_npz": str(reference),
                "profile_json": None if profile_json is None else str(profile_json),
                "pass_count": int(pass_count),
                "fail_count": int(fail_count),
                "candidate_count": int(len(case["candidates"])),
                "candidates": cand_reports,
                "motion_compensation_defaults": None
                if profile is None
                else profile.get("motion_compensation_defaults"),
            }
        )

    return {
        "summary": {
            "case_count": int(len(case_reports)),
            "candidate_count": int(total_candidates),
            "pass_count": int(total_pass),
            "fail_count": int(total_fail),
            "pass_rate": 0.0 if total_candidates == 0 else float(total_pass) / float(total_candidates),
        },
        "cases": case_reports,
    }


def run_replay_manifest(manifest_json: str) -> Dict[str, Any]:
    cases = load_replay_manifest_json(manifest_json)
    return run_replay_cases(cases)


def save_replay_report_json(out_json: str, report: Mapping[str, Any]) -> None:
    Path(out_json).write_text(json.dumps(report, indent=2), encoding="utf-8")

