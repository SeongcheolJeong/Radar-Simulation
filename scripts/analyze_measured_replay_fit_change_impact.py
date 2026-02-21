#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from avxsim.measured_replay import load_measured_replay_plan_json


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Analyze whether path-power fit lock changes can affect measured replay outputs "
            "for given measured replay plans."
        )
    )
    p.add_argument("--plan-json", action="append", required=True)
    p.add_argument("--fit-dir", action="append", required=True)
    p.add_argument("--max-evidence-per-pack", type=int, default=20)
    p.add_argument("--output-json", required=True)
    return p.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json must be object: {path}")
    return payload


def _fit_dir_tokens(fit_dirs: Sequence[str]) -> List[str]:
    tokens: List[str] = []
    for raw in fit_dirs:
        p = Path(str(raw)).expanduser()
        try:
            rp = p.resolve()
        except Exception:
            rp = p
        vals = {str(rp), str(p), p.name}
        for v in vals:
            s = str(v).strip()
            if s != "":
                tokens.append(s)
    dedup: List[str] = []
    seen = set()
    for t in tokens:
        if t in seen:
            continue
        seen.add(t)
        dedup.append(t)
    return dedup


def _scan_obj(
    obj: Any,
    trail: str,
    fit_tokens: Sequence[str],
    out: List[Dict[str, str]],
) -> None:
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            kstr = str(k)
            lkey = kstr.lower()
            if "path_power_fit" in lkey:
                out.append(
                    {
                        "trail": f"{trail}.{kstr}" if trail else kstr,
                        "reason": "key_contains_path_power_fit",
                        "value": "<key>",
                    }
                )
            _scan_obj(v, f"{trail}.{kstr}" if trail else kstr, fit_tokens, out)
        return

    if isinstance(obj, list):
        for i, v in enumerate(obj):
            _scan_obj(v, f"{trail}[{i}]", fit_tokens, out)
        return

    if isinstance(obj, str):
        sval = str(obj)
        slow = sval.lower()
        matched = False
        reason = ""
        if "path_power_fit" in slow:
            matched = True
            reason = "value_contains_path_power_fit"
        else:
            for tok in fit_tokens:
                if tok in sval:
                    matched = True
                    reason = "value_references_fit_dir"
                    break
        if matched:
            out.append(
                {
                    "trail": trail,
                    "reason": reason,
                    "value": sval,
                }
            )
        return


def _scan_manifest_and_profiles(
    manifest_json: Path,
    fit_tokens: Sequence[str],
    max_evidence: int,
) -> Tuple[int, List[Dict[str, str]], List[str], int]:
    manifest = _load_json(manifest_json)
    manifest_ev: List[Dict[str, str]] = []
    _scan_obj(manifest, trail="manifest", fit_tokens=fit_tokens, out=manifest_ev)

    cases = manifest.get("cases", [])
    candidate_count = 0
    profile_paths: List[str] = []
    if isinstance(cases, list):
        for case in cases:
            if not isinstance(case, Mapping):
                continue
            cands = case.get("candidates", [])
            if isinstance(cands, list):
                candidate_count += len(cands)
            pj = case.get("profile_json", None)
            if isinstance(pj, str) and pj.strip() != "":
                profile_paths.append(str(pj))

    profile_ev: List[Dict[str, str]] = []
    for pj in profile_paths:
        p = Path(pj)
        if not p.exists() or not p.is_file():
            continue
        payload = _load_json(p)
        _scan_obj(payload, trail=f"profile:{p}", fit_tokens=fit_tokens, out=profile_ev)

    evidence = (manifest_ev + profile_ev)[: max(1, int(max_evidence))]
    return len(manifest_ev) + len(profile_ev), evidence, profile_paths, candidate_count


def _analyze_plan(
    plan_json: Path,
    fit_tokens: Sequence[str],
    max_evidence: int,
) -> Dict[str, Any]:
    packs = load_measured_replay_plan_json(str(plan_json))
    rows: List[Dict[str, Any]] = []

    total_candidates = 0
    impacted_pack_count = 0
    for i, pack in enumerate(packs):
        manifest_json = Path(str(pack["replay_manifest_json"]))
        ev_count, evidence, profiles, cand_count = _scan_manifest_and_profiles(
            manifest_json=manifest_json,
            fit_tokens=fit_tokens,
            max_evidence=max_evidence,
        )
        impacted = ev_count > 0
        if impacted:
            impacted_pack_count += 1
        total_candidates += int(cand_count)
        rows.append(
            {
                "pack_index": int(i),
                "pack_id": str(pack.get("pack_id", f"pack_{i+1}")),
                "replay_manifest_json": str(manifest_json),
                "profile_jsons": profiles,
                "candidate_count": int(cand_count),
                "fit_dependency_detected": bool(impacted),
                "evidence_count": int(ev_count),
                "evidence": evidence,
            }
        )

    return {
        "plan_json": str(plan_json),
        "pack_count": int(len(rows)),
        "candidate_count": int(total_candidates),
        "impacted_pack_count": int(impacted_pack_count),
        "predicted_noop_for_fit_change": bool(impacted_pack_count == 0),
        "packs": rows,
    }


def main() -> None:
    args = parse_args()

    fit_tokens = _fit_dir_tokens(args.fit_dir)
    plans = [Path(p).expanduser().resolve() for p in args.plan_json]

    plan_rows: List[Dict[str, Any]] = []
    impacted_plan_count = 0
    for p in plans:
        row = _analyze_plan(
            plan_json=p,
            fit_tokens=fit_tokens,
            max_evidence=int(args.max_evidence_per_pack),
        )
        if not bool(row["predicted_noop_for_fit_change"]):
            impacted_plan_count += 1
        plan_rows.append(row)

    out = {
        "version": 1,
        "fit_dirs": [str(Path(x).expanduser().resolve()) for x in args.fit_dir],
        "fit_tokens": fit_tokens,
        "plan_count": int(len(plan_rows)),
        "impacted_plan_count": int(impacted_plan_count),
        "predicted_noop_all_plans": bool(impacted_plan_count == 0),
        "plans": plan_rows,
        "recommendation": (
            "skip_measured_replay_rerun_due_to_no_fit_dependency"
            if impacted_plan_count == 0
            else "rerun_required_for_impacted_plans"
        ),
    }

    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("Measured replay fit-change impact analysis completed.")
    print(f"  plans: {len(plan_rows)}")
    print(f"  impacted_plans: {impacted_plan_count}")
    print(f"  predicted_noop_all_plans: {out['predicted_noop_all_plans']}")
    print(f"  recommendation: {out['recommendation']}")
    print(f"  output_json: {out_json}")


if __name__ == "__main__":
    main()
