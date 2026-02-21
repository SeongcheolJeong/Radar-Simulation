#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run fit-aware measured replay batch from existing packs with ordered fit attempts "
            "and stop gate on consecutive no-gain attempts."
        )
    )
    p.add_argument(
        "--case",
        action="append",
        required=True,
        help=(
            "Case spec: label=source_pack_root or "
            "label=source_pack_root::baseline_replay_report_json"
        ),
    )
    p.add_argument("--fit-json", action="append", required=True)
    p.add_argument("--max-no-gain-attempts", type=int, default=2)
    p.add_argument("--allow-unlocked", action="store_true")
    p.add_argument("--output-root", required=True)
    p.add_argument("--output-summary-json", default=None)
    return p.parse_args()


def _run(cmd: Sequence[str], cwd: Path, env: Mapping[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), env=dict(env), capture_output=True, text=True, check=False)


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json must be object: {path}")
    return payload


def _safe_name(text: str) -> str:
    out = []
    for ch in str(text):
        if ch.isalnum() or ch in {"-", "_"}:
            out.append(ch)
        else:
            out.append("_")
    val = "".join(out).strip("_")
    return val if val else "x"


def _parse_case_spec(raw: str) -> Dict[str, str]:
    txt = str(raw).strip()
    if txt == "" or "=" not in txt:
        raise ValueError(f"invalid --case spec: {raw}")
    label, rest = txt.split("=", 1)
    label = str(label).strip()
    if label == "":
        raise ValueError(f"invalid --case label: {raw}")

    if "::" in rest:
        src, baseline = rest.split("::", 1)
    else:
        src, baseline = rest, ""
    src = str(src).strip()
    baseline = str(baseline).strip()
    if src == "":
        raise ValueError(f"invalid --case source pack root: {raw}")
    return {
        "label": label,
        "source_pack_root": src,
        "baseline_replay_report_json": baseline,
    }


def _auto_baseline_replay_report(source_pack_root: Path) -> Path:
    # <run_root>/packs/<pack_name>
    run_root = source_pack_root.parent.parent
    return run_root / "measured_replay_outputs" / source_pack_root.name / "replay_report.json"


def _replay_summary(report: Mapping[str, Any]) -> Dict[str, Any]:
    s = report.get("summary", {})
    if not isinstance(s, Mapping):
        raise ValueError("replay report missing summary object")
    return {
        "case_count": int(s.get("case_count", 0)),
        "candidate_count": int(s.get("candidate_count", 0)),
        "pass_count": int(s.get("pass_count", 0)),
        "fail_count": int(s.get("fail_count", 0)),
        "pass_rate": float(s.get("pass_rate", 0.0)),
    }


def _candidate_pass_changes(base_report: Mapping[str, Any], new_report: Mapping[str, Any]) -> int:
    base_cases = base_report.get("cases", [])
    new_cases = new_report.get("cases", [])
    if not isinstance(base_cases, list) or not isinstance(new_cases, list):
        return 0

    base_by_name: Dict[str, bool] = {}
    for case in base_cases:
        if not isinstance(case, Mapping):
            continue
        cands = case.get("candidates", [])
        if not isinstance(cands, list):
            continue
        for c in cands:
            if not isinstance(c, Mapping):
                continue
            name = str(c.get("name", "")).strip()
            if name != "":
                base_by_name[name] = bool(c.get("pass", False))

    changed = 0
    for case in new_cases:
        if not isinstance(case, Mapping):
            continue
        cands = case.get("candidates", [])
        if not isinstance(cands, list):
            continue
        for c in cands:
            if not isinstance(c, Mapping):
                continue
            name = str(c.get("name", "")).strip()
            if name == "" or name not in base_by_name:
                continue
            if bool(c.get("pass", False)) != bool(base_by_name[name]):
                changed += 1
    return int(changed)


def _attempt_gain(base_sum: Mapping[str, Any], new_sum: Mapping[str, Any]) -> Tuple[bool, Dict[str, float]]:
    pass_delta = int(new_sum["pass_count"]) - int(base_sum["pass_count"])
    fail_delta = int(new_sum["fail_count"]) - int(base_sum["fail_count"])
    pass_rate_delta = float(new_sum["pass_rate"]) - float(base_sum["pass_rate"])
    # Gain definition: primary on pass_count, tie-break by pass_rate.
    gain = (pass_delta > 0) or (pass_delta == 0 and pass_rate_delta > 0.0)
    return bool(gain), {
        "pass_count_delta": float(pass_delta),
        "fail_count_delta": float(fail_delta),
        "pass_rate_delta": float(pass_rate_delta),
    }


def _build_fit_aware_case(
    repo_root: Path,
    env: Mapping[str, str],
    source_pack_root: Path,
    fit_json: Path,
    attempt_root: Path,
    allow_unlocked: bool,
) -> Dict[str, Any]:
    pack_out = attempt_root / "packs" / f"{source_pack_root.name}_fitaware"
    fit_pack_summary = attempt_root / "fit_aware_pack_summary.json"
    cmd1 = [
        "python3",
        "scripts/build_fit_aware_pack_from_existing_pack.py",
        "--source-pack-root",
        str(source_pack_root),
        "--output-pack-root",
        str(pack_out),
        "--path-power-fit-json",
        str(fit_json),
        "--output-summary-json",
        str(fit_pack_summary),
    ]
    proc1 = _run(cmd1, cwd=repo_root, env=env)
    if proc1.returncode != 0:
        raise RuntimeError(
            f"fit-aware pack build failed:\nSTDOUT:\n{proc1.stdout}\nSTDERR:\n{proc1.stderr}"
        )

    plan_json = attempt_root / "measured_replay_plan.json"
    cmd2 = [
        "python3",
        "scripts/build_measured_replay_plan.py",
        "--packs-root",
        str(attempt_root / "packs"),
        "--output-plan-json",
        str(plan_json),
    ]
    proc2 = _run(cmd2, cwd=repo_root, env=env)
    if proc2.returncode != 0:
        raise RuntimeError(
            f"measured replay plan build failed:\nSTDOUT:\n{proc2.stdout}\nSTDERR:\n{proc2.stderr}"
        )

    replay_out = attempt_root / "measured_replay_outputs"
    replay_summary_json = attempt_root / "measured_replay_summary.json"
    cmd3 = [
        "python3",
        "scripts/run_measured_replay_execution.py",
        "--plan-json",
        str(plan_json),
        "--output-root",
        str(replay_out),
        "--output-summary-json",
        str(replay_summary_json),
    ]
    if allow_unlocked:
        cmd3.append("--allow-unlocked")
    proc3 = _run(cmd3, cwd=repo_root, env=env)
    if proc3.returncode not in (0, 2):
        raise RuntimeError(
            f"measured replay run failed:\nSTDOUT:\n{proc3.stdout}\nSTDERR:\n{proc3.stderr}"
        )

    summary = _load_json(replay_summary_json)
    packs = summary.get("packs", [])
    if not isinstance(packs, list) or len(packs) == 0:
        raise ValueError(f"invalid measured replay summary: {replay_summary_json}")
    replay_report_json = Path(str(packs[0].get("replay_report_json", "")))
    if not replay_report_json.exists():
        raise FileNotFoundError(f"missing replay_report_json: {replay_report_json}")

    return {
        "fit_pack_summary_json": str(fit_pack_summary),
        "measured_replay_plan_json": str(plan_json),
        "measured_replay_summary_json": str(replay_summary_json),
        "replay_report_json": str(replay_report_json),
        "measured_replay_exit_code": int(proc3.returncode),
    }


def main() -> None:
    args = parse_args()
    if int(args.max_no_gain_attempts) <= 0:
        raise ValueError("--max-no-gain-attempts must be positive")

    repo_root = Path(__file__).resolve().parents[1]
    out_root = Path(args.output_root)
    out_root.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    fit_jsons = [Path(p).expanduser().resolve() for p in args.fit_json]
    if len(fit_jsons) == 0:
        raise ValueError("--fit-json must be non-empty")
    for f in fit_jsons:
        if not f.exists() or not f.is_file():
            raise FileNotFoundError(f"fit json not found: {f}")

    case_specs = [_parse_case_spec(x) for x in args.case]

    case_rows: List[Dict[str, Any]] = []
    improved_case_count = 0

    for ci, spec in enumerate(case_specs):
        label = str(spec["label"])
        source_pack_root = Path(spec["source_pack_root"]).expanduser().resolve()
        if not source_pack_root.exists() or not source_pack_root.is_dir():
            raise FileNotFoundError(f"source pack root not found: {source_pack_root}")

        baseline_report_json = (
            Path(spec["baseline_replay_report_json"]).expanduser().resolve()
            if str(spec["baseline_replay_report_json"]).strip() != ""
            else _auto_baseline_replay_report(source_pack_root)
        )
        if not baseline_report_json.exists() or not baseline_report_json.is_file():
            raise FileNotFoundError(
                f"baseline replay report not found for case '{label}': {baseline_report_json}"
            )

        baseline_report = _load_json(baseline_report_json)
        baseline_sum = _replay_summary(baseline_report)

        case_out = out_root / f"case_{ci:02d}_{_safe_name(label)}"
        case_out.mkdir(parents=True, exist_ok=True)

        attempts: List[Dict[str, Any]] = []
        consecutive_no_gain = 0
        stop_reason = "fit_list_exhausted"
        best_idx = -1
        best_key: Tuple[float, float] = (-1e18, -1e18)

        for ai, fit_json in enumerate(fit_jsons):
            attempt_id = f"attempt_{ai:02d}_{_safe_name(fit_json.stem)}"
            attempt_root = case_out / attempt_id
            attempt_root.mkdir(parents=True, exist_ok=True)

            run_out = _build_fit_aware_case(
                repo_root=repo_root,
                env=env,
                source_pack_root=source_pack_root,
                fit_json=fit_json,
                attempt_root=attempt_root,
                allow_unlocked=bool(args.allow_unlocked),
            )

            new_report = _load_json(Path(run_out["replay_report_json"]))
            new_sum = _replay_summary(new_report)
            gain, delta = _attempt_gain(base_sum=baseline_sum, new_sum=new_sum)
            pass_changed = _candidate_pass_changes(base_report=baseline_report, new_report=new_report)

            if gain:
                consecutive_no_gain = 0
            else:
                consecutive_no_gain += 1

            key = (float(delta["pass_count_delta"]), float(delta["pass_rate_delta"]))
            if key > best_key:
                best_key = key
                best_idx = ai

            row = {
                "attempt_index": int(ai),
                "attempt_id": attempt_id,
                "fit_json": str(fit_json),
                "output_root": str(attempt_root),
                "baseline_summary": baseline_sum,
                "replay_summary": new_sum,
                "delta": delta,
                "candidate_pass_status_changed": int(pass_changed),
                "gain": bool(gain),
                "consecutive_no_gain_after_attempt": int(consecutive_no_gain),
            }
            row.update(run_out)
            attempts.append(row)

            if consecutive_no_gain >= int(args.max_no_gain_attempts):
                stop_reason = "max_no_gain_reached"
                break

        if best_idx >= 0 and attempts[best_idx]["gain"]:
            improved_case_count += 1

        case_rows.append(
            {
                "case_index": int(ci),
                "label": label,
                "source_pack_root": str(source_pack_root),
                "baseline_replay_report_json": str(baseline_report_json),
                "baseline_summary": baseline_sum,
                "fit_attempt_count": int(len(attempts)),
                "stop_reason": stop_reason,
                "max_no_gain_attempts": int(args.max_no_gain_attempts),
                "best_attempt_index": int(best_idx),
                "best_attempt": None if best_idx < 0 else attempts[best_idx],
                "improved_over_baseline": bool(best_idx >= 0 and attempts[best_idx]["gain"]),
                "attempts": attempts,
            }
        )

    summary = {
        "version": 1,
        "fit_jsons": [str(x) for x in fit_jsons],
        "max_no_gain_attempts": int(args.max_no_gain_attempts),
        "allow_unlocked": bool(args.allow_unlocked),
        "case_count": int(len(case_rows)),
        "improved_case_count": int(improved_case_count),
        "cases": case_rows,
    }

    out_summary = (
        out_root / "fit_aware_measured_replay_batch_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json)
    )
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    out_summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Fit-aware measured replay batch completed.")
    print(f"  case_count: {summary['case_count']}")
    print(f"  improved_case_count: {summary['improved_case_count']}")
    print(f"  output_summary_json: {out_summary}")


if __name__ == "__main__":
    main()
