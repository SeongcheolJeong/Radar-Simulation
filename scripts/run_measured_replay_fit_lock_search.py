#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run measured replay fit-lock search with policy selection and short-circuit on "
            "impossible improvement headroom."
        )
    )
    p.add_argument(
        "--case",
        action="append",
        required=True,
        help="Case spec: label=source_pack_root or label=source_pack_root::baseline_replay_report_json",
    )
    p.add_argument("--fit-json", action="append", default=[])
    p.add_argument("--fit-dir", action="append", default=[])
    p.add_argument("--fit-glob", default="path_power_fit_*selected.json")

    p.add_argument("--baseline-mode", choices=["rerun", "provided"], default="rerun")
    p.add_argument(
        "--disable-short-circuit-on-impossible",
        action="store_true",
        help="Disable short-circuit and force full fit-aware batch execution.",
    )

    p.add_argument("--max-pass-rate-drop", type=float, default=0.0)
    p.add_argument("--max-pass-count-drop", type=int, default=0)
    p.add_argument("--max-fail-count-increase", type=int, default=0)
    p.add_argument("--min-improved-cases", type=int, default=1)
    p.add_argument("--require-full-case-coverage", action="store_true")

    p.add_argument("--fit-proxy-max-range-exp", type=float, default=None)
    p.add_argument("--fit-proxy-max-azimuth-power", type=float, default=None)
    p.add_argument("--fit-proxy-min-weight", type=float, default=None)
    p.add_argument("--fit-proxy-max-weight", type=float, default=None)
    p.add_argument("--reference-anchor", choices=["source", "rebuilt"], default="source")

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


def _as_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except (TypeError, ValueError):
        return int(default)


def _as_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return float(default)


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
    run_root = source_pack_root.parent.parent
    return run_root / "measured_replay_outputs" / source_pack_root.name / "replay_report.json"


def _resolve_baseline_report_path_from_summary(
    replay_summary_json: Path,
    source_pack_root: Path,
) -> Path:
    summary = _load_json(replay_summary_json)
    packs = summary.get("packs", [])
    if not isinstance(packs, list) or len(packs) == 0:
        raise ValueError(f"invalid measured replay summary: {replay_summary_json}")
    target_name = str(source_pack_root.name)

    for row in packs:
        if not isinstance(row, Mapping):
            continue
        rr = Path(str(row.get("replay_report_json", "")))
        if rr.exists() and target_name in str(rr):
            return rr

    rr0 = Path(str(packs[0].get("replay_report_json", "")))
    if not rr0.exists():
        raise FileNotFoundError(f"missing replay_report_json in summary: {replay_summary_json}")
    return rr0


def _replay_summary(report: Mapping[str, Any]) -> Dict[str, Any]:
    s = report.get("summary", {})
    if not isinstance(s, Mapping):
        raise ValueError("replay report missing summary object")
    return {
        "case_count": _as_int(s.get("case_count", 0)),
        "candidate_count": _as_int(s.get("candidate_count", 0)),
        "pass_count": _as_int(s.get("pass_count", 0)),
        "fail_count": _as_int(s.get("fail_count", 0)),
        "pass_rate": _as_float(s.get("pass_rate", 0.0)),
    }


def _collect_fit_jsons(args: argparse.Namespace) -> List[Path]:
    out: List[Path] = []
    seen = set()

    for raw in args.fit_json:
        p = Path(raw).expanduser().resolve()
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"fit json not found: {p}")
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)

    for d in args.fit_dir:
        root = Path(d).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(f"fit dir not found: {root}")
        for p in sorted(root.glob(str(args.fit_glob))):
            if not p.is_file():
                continue
            key = str(p.resolve())
            if key in seen:
                continue
            seen.add(key)
            out.append(p.resolve())

    if len(out) == 0:
        raise ValueError("no fit json candidates found")
    return out


def _build_current_baseline_case(
    repo_root: Path,
    env: Mapping[str, str],
    source_pack_root: Path,
    case_out: Path,
    allow_unlocked: bool,
) -> Dict[str, Any]:
    baseline_root = case_out / "baseline_current"
    baseline_root.mkdir(parents=True, exist_ok=True)

    plan_json = baseline_root / "measured_replay_plan.json"
    cmd1 = [
        "python3",
        "scripts/build_measured_replay_plan.py",
        "--packs-root",
        str(source_pack_root.parent),
        "--output-plan-json",
        str(plan_json),
    ]
    proc1 = _run(cmd1, cwd=repo_root, env=env)
    if proc1.returncode != 0:
        raise RuntimeError(
            f"baseline plan build failed:\nSTDOUT:\n{proc1.stdout}\nSTDERR:\n{proc1.stderr}"
        )

    replay_out = baseline_root / "measured_replay_outputs"
    replay_summary_json = baseline_root / "measured_replay_summary.json"
    cmd2 = [
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
        cmd2.append("--allow-unlocked")
    proc2 = _run(cmd2, cwd=repo_root, env=env)
    if proc2.returncode not in (0, 2):
        raise RuntimeError(
            f"baseline replay run failed:\nSTDOUT:\n{proc2.stdout}\nSTDERR:\n{proc2.stderr}"
        )

    replay_report_json = _resolve_baseline_report_path_from_summary(
        replay_summary_json=replay_summary_json,
        source_pack_root=source_pack_root,
    )
    report = _load_json(replay_report_json)
    return {
        "baseline_replay_report_json": str(replay_report_json),
        "baseline_plan_json": str(plan_json),
        "baseline_measured_replay_summary_json": str(replay_summary_json),
        "baseline_measured_replay_exit_code": int(proc2.returncode),
        "baseline_summary": _replay_summary(report),
    }


def main() -> None:
    args = parse_args()
    if _as_float(args.max_pass_rate_drop) < 0.0:
        raise ValueError("--max-pass-rate-drop must be >= 0")
    if _as_int(args.max_pass_count_drop) < 0:
        raise ValueError("--max-pass-count-drop must be >= 0")
    if _as_int(args.max_fail_count_increase) < 0:
        raise ValueError("--max-fail-count-increase must be >= 0")
    if _as_int(args.min_improved_cases) < 0:
        raise ValueError("--min-improved-cases must be >= 0")

    repo_root = Path(__file__).resolve().parents[1]
    out_root = Path(args.output_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    fit_jsons = _collect_fit_jsons(args)
    case_specs = [_parse_case_spec(x) for x in args.case]

    baseline_rows: List[Dict[str, Any]] = []
    cases_with_headroom = 0
    for ci, spec in enumerate(case_specs):
        label = str(spec["label"])
        source_pack_root = Path(spec["source_pack_root"]).expanduser().resolve()
        if not source_pack_root.exists() or not source_pack_root.is_dir():
            raise FileNotFoundError(f"source pack root not found: {source_pack_root}")

        case_out = out_root / f"case_{ci:02d}_{label}"
        case_out.mkdir(parents=True, exist_ok=True)

        if str(args.baseline_mode) == "rerun":
            row = _build_current_baseline_case(
                repo_root=repo_root,
                env=env,
                source_pack_root=source_pack_root,
                case_out=case_out,
                allow_unlocked=bool(args.allow_unlocked),
            )
        else:
            baseline_report_json = (
                Path(spec["baseline_replay_report_json"]).expanduser().resolve()
                if str(spec["baseline_replay_report_json"]).strip() != ""
                else _auto_baseline_replay_report(source_pack_root)
            )
            if not baseline_report_json.exists() or not baseline_report_json.is_file():
                raise FileNotFoundError(
                    f"baseline replay report not found for case '{label}': {baseline_report_json}"
                )
            report = _load_json(baseline_report_json)
            row = {
                "baseline_replay_report_json": str(baseline_report_json),
                "baseline_summary": _replay_summary(report),
            }

        summary = row["baseline_summary"]
        if int(summary["fail_count"]) > 0 or float(summary["pass_rate"]) < 1.0:
            cases_with_headroom += 1

        baseline_rows.append(
            {
                "case_index": int(ci),
                "label": label,
                "source_pack_root": str(source_pack_root),
                **row,
            }
        )

    short_circuit = (
        (not bool(args.disable_short_circuit_on_impossible))
        and int(args.min_improved_cases) > int(cases_with_headroom)
    )

    batch_summary_json = out_root / "fit_aware_measured_replay_batch_summary.json"
    selection_json = out_root / "measured_replay_fit_lock_selection.json"
    policy_gate_json = out_root / "fit_aware_policy_gate_summary.json"

    if short_circuit:
        selection_payload = {
            "version": 1,
            "input_batch_summary_json": None,
            "batch_metadata": {
                "baseline_mode": str(args.baseline_mode),
                "case_count": int(len(case_specs)),
                "fit_json_count": int(len(fit_jsons)),
                "short_circuit": True,
            },
            "policy": {
                "max_pass_rate_drop": float(args.max_pass_rate_drop),
                "max_pass_count_drop": int(args.max_pass_count_drop),
                "max_fail_count_increase": int(args.max_fail_count_increase),
                "min_improved_cases": int(args.min_improved_cases),
                "require_full_case_coverage": bool(args.require_full_case_coverage),
                "fallback_mode": "baseline_no_fit",
            },
            "selection": {
                "selection_mode": "baseline_no_fit",
                "recommendation": "fallback_to_baseline_no_fit",
                "selected_fit_json": None,
                "selected_fit_summary": None,
                "short_circuit_reason": "insufficient_improvement_headroom",
            },
            "fit_candidates": [
                {
                    "fit_json": str(p),
                    "eligible": False,
                    "rejected_reasons": ["search_short_circuited_no_headroom"],
                }
                for p in fit_jsons
            ],
        }
        selection_json.write_text(json.dumps(selection_payload, indent=2), encoding="utf-8")

        out = {
            "version": 1,
            "baseline_mode": str(args.baseline_mode),
            "case_count": int(len(case_specs)),
            "fit_json_count": int(len(fit_jsons)),
            "cases_with_improvement_headroom": int(cases_with_headroom),
            "policy": {
                "min_improved_cases": int(args.min_improved_cases),
                "max_pass_rate_drop": float(args.max_pass_rate_drop),
                "max_pass_count_drop": int(args.max_pass_count_drop),
                "max_fail_count_increase": int(args.max_fail_count_increase),
                "require_full_case_coverage": bool(args.require_full_case_coverage),
            },
            "short_circuit": True,
            "short_circuit_reason": "insufficient_improvement_headroom",
            "fit_jsons": [str(x) for x in fit_jsons],
            "baseline_cases": baseline_rows,
            "batch_summary_json": None,
            "policy_gate_json": None,
            "selection_json": str(selection_json),
            "selection": selection_payload["selection"],
        }
    else:
        cmd_batch = [
            "python3",
            "scripts/run_fit_aware_measured_replay_batch.py",
            "--baseline-mode",
            str(args.baseline_mode),
            "--max-no-gain-attempts",
            str(int(args.max_no_gain_attempts)),
            "--reference-anchor",
            str(args.reference_anchor),
            "--output-root",
            str(out_root / "fit_aware_batch_run"),
            "--output-summary-json",
            str(batch_summary_json),
        ]
        for spec in case_specs:
            raw = f"{spec['label']}={spec['source_pack_root']}"
            if str(spec["baseline_replay_report_json"]).strip() != "":
                raw += f"::{spec['baseline_replay_report_json']}"
            cmd_batch.extend(["--case", raw])
        for fit_json in fit_jsons:
            cmd_batch.extend(["--fit-json", str(fit_json)])
        if args.fit_proxy_max_range_exp is not None:
            cmd_batch.extend(["--fit-proxy-max-range-exp", str(float(args.fit_proxy_max_range_exp))])
        if args.fit_proxy_max_azimuth_power is not None:
            cmd_batch.extend(["--fit-proxy-max-azimuth-power", str(float(args.fit_proxy_max_azimuth_power))])
        if args.fit_proxy_min_weight is not None:
            cmd_batch.extend(["--fit-proxy-min-weight", str(float(args.fit_proxy_min_weight))])
        if args.fit_proxy_max_weight is not None:
            cmd_batch.extend(["--fit-proxy-max-weight", str(float(args.fit_proxy_max_weight))])
        if args.allow_unlocked:
            cmd_batch.append("--allow-unlocked")

        p_batch = _run(cmd_batch, cwd=repo_root, env=env)
        if p_batch.returncode != 0:
            raise RuntimeError(f"fit-aware batch failed:\nSTDOUT:\n{p_batch.stdout}\nSTDERR:\n{p_batch.stderr}")

        cmd_gate = [
            "python3",
            "scripts/evaluate_fit_aware_replay_policy_gate.py",
            "--batch-summary-json",
            str(batch_summary_json),
            "--output-json",
            str(policy_gate_json),
            "--max-pass-rate-drop",
            str(float(args.max_pass_rate_drop)),
            "--max-pass-count-drop",
            str(int(args.max_pass_count_drop)),
            "--max-fail-count-increase",
            str(int(args.max_fail_count_increase)),
            "--min-improved-cases",
            str(int(args.min_improved_cases)),
            "--require-non-degradation-all-cases",
        ]
        p_gate = _run(cmd_gate, cwd=repo_root, env=env)
        if p_gate.returncode != 0:
            raise RuntimeError(f"policy gate failed:\nSTDOUT:\n{p_gate.stdout}\nSTDERR:\n{p_gate.stderr}")

        cmd_sel = [
            "python3",
            "scripts/select_measured_replay_fit_lock_by_policy.py",
            "--batch-summary-json",
            str(batch_summary_json),
            "--output-json",
            str(selection_json),
            "--max-pass-rate-drop",
            str(float(args.max_pass_rate_drop)),
            "--max-pass-count-drop",
            str(int(args.max_pass_count_drop)),
            "--max-fail-count-increase",
            str(int(args.max_fail_count_increase)),
            "--min-improved-cases",
            str(int(args.min_improved_cases)),
        ]
        if args.require_full_case_coverage:
            cmd_sel.append("--require-full-case-coverage")
        p_sel = _run(cmd_sel, cwd=repo_root, env=env)
        if p_sel.returncode != 0:
            raise RuntimeError(f"policy selector failed:\nSTDOUT:\n{p_sel.stdout}\nSTDERR:\n{p_sel.stderr}")

        selection_payload = _load_json(selection_json)
        gate_payload = _load_json(policy_gate_json)
        out = {
            "version": 1,
            "baseline_mode": str(args.baseline_mode),
            "case_count": int(len(case_specs)),
            "fit_json_count": int(len(fit_jsons)),
            "cases_with_improvement_headroom": int(cases_with_headroom),
            "policy": {
                "min_improved_cases": int(args.min_improved_cases),
                "max_pass_rate_drop": float(args.max_pass_rate_drop),
                "max_pass_count_drop": int(args.max_pass_count_drop),
                "max_fail_count_increase": int(args.max_fail_count_increase),
                "require_full_case_coverage": bool(args.require_full_case_coverage),
            },
            "short_circuit": False,
            "fit_jsons": [str(x) for x in fit_jsons],
            "baseline_cases": baseline_rows,
            "batch_summary_json": str(batch_summary_json),
            "policy_gate_json": str(policy_gate_json),
            "selection_json": str(selection_json),
            "policy_gate": {
                "gate_failed": bool(gate_payload.get("gate_failed", True)),
                "recommendation": str(gate_payload.get("recommendation", "")),
            },
            "selection": selection_payload.get("selection", {}),
        }

    out_summary_json = (
        out_root / "measured_replay_fit_lock_search_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json).expanduser().resolve()
    )
    out_summary_json.parent.mkdir(parents=True, exist_ok=True)
    out_summary_json.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("Measured replay fit-lock search completed.")
    print(f"  case_count: {out['case_count']}")
    print(f"  fit_json_count: {out['fit_json_count']}")
    print(f"  cases_with_improvement_headroom: {out['cases_with_improvement_headroom']}")
    print(f"  short_circuit: {out['short_circuit']}")
    print(f"  selection_mode: {out['selection'].get('selection_mode')}")
    print(f"  recommendation: {out['selection'].get('recommendation')}")
    print(f"  output_summary_json: {out_summary_json}")


if __name__ == "__main__":
    main()
