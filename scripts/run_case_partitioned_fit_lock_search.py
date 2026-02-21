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
            "Run global fit-lock search first and fallback to family-partitioned search "
            "when global selection is not fit."
        )
    )
    p.add_argument(
        "--case",
        action="append",
        required=True,
        help="Case spec: label=source_pack_root or label=source_pack_root::baseline_replay_report_json",
    )
    p.add_argument(
        "--case-family",
        action="append",
        required=True,
        help="Family mapping: label=family_name",
    )

    p.add_argument("--fit-json", action="append", default=[])
    p.add_argument("--fit-dir", action="append", default=[])
    p.add_argument("--fit-glob", default="path_power_fit_*selected.json")

    p.add_argument(
        "--global-search-summary-json",
        default=None,
        help="Optional existing global fit-lock search summary. If provided, skip global run.",
    )

    p.add_argument("--baseline-mode", choices=["rerun", "provided"], default="provided")
    p.add_argument("--objective-mode", choices=["auto", "improvement", "drift"], default="drift")
    p.add_argument("--max-no-gain-attempts", type=int, default=2)
    p.add_argument("--require-full-case-coverage", action="store_true")

    p.add_argument("--drift-metric", action="append", default=[])
    p.add_argument("--drift-quantile", type=float, default=0.9)
    p.add_argument("--drift-weight-pass-rate-drop", type=float, default=100.0)
    p.add_argument("--drift-weight-pass-count-drop-ratio", type=float, default=20.0)
    p.add_argument("--drift-weight-fail-count-increase-ratio", type=float, default=20.0)
    p.add_argument("--drift-weight-metric-drift", type=float, default=1.0)
    p.add_argument("--drift-max-pass-rate-drop", type=float, default=1.0)
    p.add_argument("--drift-max-pass-count-drop-ratio", type=float, default=1.0)
    p.add_argument("--drift-max-fail-count-increase-ratio", type=float, default=1.0)
    p.add_argument("--drift-max-metric-drift", type=float, default=1e9)

    p.add_argument("--fit-proxy-max-range-exp", type=float, default=None)
    p.add_argument("--fit-proxy-max-azimuth-power", type=float, default=None)
    p.add_argument("--fit-proxy-min-weight", type=float, default=None)
    p.add_argument("--fit-proxy-max-weight", type=float, default=None)

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


def _parse_label_value(raw: str, field_name: str) -> Dict[str, str]:
    txt = str(raw).strip()
    if txt == "" or "=" not in txt:
        raise ValueError(f"invalid {field_name} spec: {raw}")
    label, value = txt.split("=", 1)
    label = str(label).strip()
    value = str(value).strip()
    if label == "" or value == "":
        raise ValueError(f"invalid {field_name} label/value: {raw}")
    return {"label": label, "value": value}


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


def _build_search_cmd(
    args: argparse.Namespace,
    cases: Sequence[Mapping[str, str]],
    fit_jsons: Sequence[Path],
    output_root: Path,
    output_summary_json: Path,
) -> List[str]:
    cmd = [
        "python3",
        "scripts/run_measured_replay_fit_lock_search.py",
        "--baseline-mode",
        str(args.baseline_mode),
        "--objective-mode",
        str(args.objective_mode),
        "--max-no-gain-attempts",
        str(int(args.max_no_gain_attempts)),
        "--drift-quantile",
        str(float(args.drift_quantile)),
        "--drift-weight-pass-rate-drop",
        str(float(args.drift_weight_pass_rate_drop)),
        "--drift-weight-pass-count-drop-ratio",
        str(float(args.drift_weight_pass_count_drop_ratio)),
        "--drift-weight-fail-count-increase-ratio",
        str(float(args.drift_weight_fail_count_increase_ratio)),
        "--drift-weight-metric-drift",
        str(float(args.drift_weight_metric_drift)),
        "--drift-max-pass-rate-drop",
        str(float(args.drift_max_pass_rate_drop)),
        "--drift-max-pass-count-drop-ratio",
        str(float(args.drift_max_pass_count_drop_ratio)),
        "--drift-max-fail-count-increase-ratio",
        str(float(args.drift_max_fail_count_increase_ratio)),
        "--drift-max-metric-drift",
        str(float(args.drift_max_metric_drift)),
        "--output-root",
        str(output_root),
        "--output-summary-json",
        str(output_summary_json),
    ]
    if args.require_full_case_coverage:
        cmd.append("--require-full-case-coverage")
    for m in args.drift_metric:
        cmd.extend(["--drift-metric", str(m)])
    if args.fit_proxy_max_range_exp is not None:
        cmd.extend(["--fit-proxy-max-range-exp", str(float(args.fit_proxy_max_range_exp))])
    if args.fit_proxy_max_azimuth_power is not None:
        cmd.extend(["--fit-proxy-max-azimuth-power", str(float(args.fit_proxy_max_azimuth_power))])
    if args.fit_proxy_min_weight is not None:
        cmd.extend(["--fit-proxy-min-weight", str(float(args.fit_proxy_min_weight))])
    if args.fit_proxy_max_weight is not None:
        cmd.extend(["--fit-proxy-max-weight", str(float(args.fit_proxy_max_weight))])
    if args.allow_unlocked:
        cmd.append("--allow-unlocked")

    for spec in cases:
        raw = f"{spec['label']}={spec['source_pack_root']}"
        baseline = str(spec.get("baseline_replay_report_json", "")).strip()
        if baseline != "":
            raw += f"::{baseline}"
        cmd.extend(["--case", raw])
    for fit_json in fit_jsons:
        cmd.extend(["--fit-json", str(fit_json)])
    return cmd


def _run_search(
    repo_root: Path,
    env: Mapping[str, str],
    args: argparse.Namespace,
    cases: Sequence[Mapping[str, str]],
    fit_jsons: Sequence[Path],
    run_root: Path,
    run_id: str,
) -> Dict[str, Any]:
    out_root = run_root / run_id
    out_root.mkdir(parents=True, exist_ok=True)
    summary_json = out_root / "fit_lock_search_summary.json"
    cmd = _build_search_cmd(
        args=args,
        cases=cases,
        fit_jsons=fit_jsons,
        output_root=out_root,
        output_summary_json=summary_json,
    )
    proc = _run(cmd, cwd=repo_root, env=env)
    if proc.returncode != 0:
        raise RuntimeError(
            f"fit-lock search failed ({run_id}):\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    payload = _load_json(summary_json)
    payload["_search_summary_json"] = str(summary_json)
    return payload


def _selection(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    sel = payload.get("selection", {})
    if not isinstance(sel, Mapping):
        return {}
    return sel


def main() -> None:
    args = parse_args()
    if int(args.max_no_gain_attempts) < 0:
        raise ValueError("--max-no-gain-attempts must be >= 0")
    if not (0.0 < float(args.drift_quantile) < 1.0):
        raise ValueError("--drift-quantile must be in (0,1)")
    if float(args.drift_max_pass_rate_drop) < 0.0:
        raise ValueError("--drift-max-pass-rate-drop must be >= 0")
    if float(args.drift_max_pass_count_drop_ratio) < 0.0:
        raise ValueError("--drift-max-pass-count-drop-ratio must be >= 0")
    if float(args.drift_max_fail_count_increase_ratio) < 0.0:
        raise ValueError("--drift-max-fail-count-increase-ratio must be >= 0")
    if float(args.drift_max_metric_drift) < 0.0:
        raise ValueError("--drift-max-metric-drift must be >= 0")

    repo_root = Path(__file__).resolve().parents[1]
    out_root = Path(args.output_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    cases = [_parse_case_spec(x) for x in args.case]
    case_labels = [str(x["label"]) for x in cases]
    case_families_raw = [_parse_label_value(x, "--case-family") for x in args.case_family]
    case_family_map: Dict[str, str] = {str(x["label"]): str(x["value"]) for x in case_families_raw}

    missing_family = [x for x in case_labels if x not in case_family_map]
    if len(missing_family) > 0:
        raise ValueError(f"missing --case-family for labels: {missing_family}")

    fit_jsons = _collect_fit_jsons(args)
    run_root = out_root / "search_runs"
    run_root.mkdir(parents=True, exist_ok=True)

    reused_global = False
    if args.global_search_summary_json is not None:
        global_summary_json = Path(args.global_search_summary_json).expanduser().resolve()
        if not global_summary_json.exists() or not global_summary_json.is_file():
            raise FileNotFoundError(f"global search summary not found: {global_summary_json}")
        global_payload = _load_json(global_summary_json)
        global_payload["_search_summary_json"] = str(global_summary_json)
        reused_global = True
    else:
        global_payload = _run_search(
            repo_root=repo_root,
            env=env,
            args=args,
            cases=cases,
            fit_jsons=fit_jsons,
            run_root=run_root,
            run_id="global",
        )

    global_sel = _selection(global_payload)
    global_selection_mode = str(global_sel.get("selection_mode", ""))
    global_recommendation = str(global_sel.get("recommendation", ""))
    global_selected_fit_json = global_sel.get("selected_fit_json", None)

    family_rows: List[Dict[str, Any]] = []
    families = sorted(set(case_family_map.values()))

    if global_selection_mode != "fit":
        for fam in families:
            fam_cases = [x for x in cases if case_family_map.get(str(x["label"])) == fam]
            fam_payload = _run_search(
                repo_root=repo_root,
                env=env,
                args=args,
                cases=fam_cases,
                fit_jsons=fit_jsons,
                run_root=run_root,
                run_id=f"family_{fam}",
            )
            fam_sel = _selection(fam_payload)
            family_rows.append(
                {
                    "family": fam,
                    "case_labels": [str(x["label"]) for x in fam_cases],
                    "search_summary_json": str(fam_payload.get("_search_summary_json")),
                    "selection_mode": str(fam_sel.get("selection_mode", "")),
                    "recommendation": str(fam_sel.get("recommendation", "")),
                    "selected_fit_json": fam_sel.get("selected_fit_json", None),
                }
            )

    fit_families = [x for x in family_rows if str(x.get("selection_mode", "")) == "fit"]

    if global_selection_mode == "fit":
        strategy = "global_fit_lock"
        final_selection_mode = "fit"
        final_selected_fit_json = global_selected_fit_json
        selected_by_family = {fam: global_selected_fit_json for fam in families}
    elif len(fit_families) == len(families) and len(families) > 0:
        strategy = "family_partitioned_fit_lock"
        final_selection_mode = "fit_partitioned"
        final_selected_fit_json = None
        selected_by_family = {str(x["family"]): x.get("selected_fit_json", None) for x in family_rows}
    elif len(fit_families) > 0:
        strategy = "mixed_family_partitioned_lock"
        final_selection_mode = "fit_partitioned_with_baseline_fallback"
        final_selected_fit_json = None
        selected_by_family = {
            str(x["family"]): (
                x.get("selected_fit_json", None) if str(x.get("selection_mode", "")) == "fit" else None
            )
            for x in family_rows
        }
    else:
        strategy = "baseline_no_fit"
        final_selection_mode = "baseline_no_fit"
        final_selected_fit_json = None
        selected_by_family = {fam: None for fam in families}

    out = {
        "version": 1,
        "case_count": int(len(cases)),
        "family_count": int(len(families)),
        "fit_json_count": int(len(fit_jsons)),
        "baseline_mode": str(args.baseline_mode),
        "objective_mode": str(args.objective_mode),
        "reused_global_search_summary": bool(reused_global),
        "global_search_summary_json": str(global_payload.get("_search_summary_json")),
        "global_selection": {
            "selection_mode": global_selection_mode,
            "recommendation": global_recommendation,
            "selected_fit_json": global_selected_fit_json,
        },
        "families": family_rows,
        "final": {
            "strategy": strategy,
            "selection_mode": final_selection_mode,
            "selected_fit_json": final_selected_fit_json,
            "selected_fit_by_family": selected_by_family,
        },
        "case_family_map": case_family_map,
        "fit_jsons": [str(x) for x in fit_jsons],
    }

    out_summary_json = (
        out_root / "case_partitioned_fit_lock_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json).expanduser().resolve()
    )
    out_summary_json.parent.mkdir(parents=True, exist_ok=True)
    out_summary_json.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("Case-partitioned fit-lock search completed.")
    print(f"  case_count: {out['case_count']}")
    print(f"  family_count: {out['family_count']}")
    print(f"  fit_json_count: {out['fit_json_count']}")
    print(f"  reused_global_search_summary: {out['reused_global_search_summary']}")
    print(f"  global_selection_mode: {out['global_selection']['selection_mode']}")
    print(f"  final_strategy: {out['final']['strategy']}")
    print(f"  output_summary_json: {out_summary_json}")


if __name__ == "__main__":
    main()
