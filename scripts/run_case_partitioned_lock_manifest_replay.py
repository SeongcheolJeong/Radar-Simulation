#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from avxsim.measured_replay import (
    run_measured_replay_plan,
    save_measured_replay_summary_json,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Materialize family-partitioned fit-lock policy into case-level lock manifest "
            "and run measured replay verification."
        )
    )
    p.add_argument("--case-partitioned-summary-json", required=True)
    p.add_argument(
        "--case",
        action="append",
        required=True,
        help="Case spec: label=source_pack_root or label=source_pack_root::baseline_replay_report_json",
    )
    p.add_argument(
        "--reference-anchor",
        choices=["source", "rebuilt"],
        default="source",
        help="Reference NPZ anchor used when rebuilding fit-aware packs.",
    )
    p.add_argument("--fit-proxy-max-range-exp", type=float, default=None)
    p.add_argument("--fit-proxy-max-azimuth-power", type=float, default=None)
    p.add_argument("--fit-proxy-min-weight", type=float, default=None)
    p.add_argument("--fit-proxy-max-weight", type=float, default=None)
    p.add_argument("--default-min-pass-rate", type=float, default=1.0)
    p.add_argument("--default-max-case-fail-count", type=int, default=0)
    p.add_argument("--default-require-motion-defaults-enabled", action="store_true")
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


def _save_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), indent=2), encoding="utf-8")


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


def _safe_name(text: str) -> str:
    out = []
    for ch in str(text):
        if ch.isalnum() or ch in {"-", "_"}:
            out.append(ch)
        else:
            out.append("_")
    val = "".join(out).strip("_")
    return val if val else "x"


def _auto_baseline_replay_report(source_pack_root: Path) -> Path:
    run_root = source_pack_root.parent.parent
    return run_root / "measured_replay_outputs" / source_pack_root.name / "replay_report.json"


def _load_lock_policy(pack_root: Path) -> Optional[Dict[str, Any]]:
    p = pack_root / "lock_policy.json"
    if not p.exists() or not p.is_file():
        return None
    payload = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"lock policy must be object: {p}")
    return dict(payload)


def _summary_from_replay_report(payload: Mapping[str, Any]) -> Dict[str, float]:
    s = payload.get("summary", {})
    if not isinstance(s, Mapping):
        return {
            "case_count": 0.0,
            "candidate_count": 0.0,
            "pass_count": 0.0,
            "fail_count": 0.0,
            "pass_rate": 0.0,
        }
    return {
        "case_count": float(s.get("case_count", 0)),
        "candidate_count": float(s.get("candidate_count", 0)),
        "pass_count": float(s.get("pass_count", 0)),
        "fail_count": float(s.get("fail_count", 0)),
        "pass_rate": float(s.get("pass_rate", 0.0)),
    }


def _build_fit_proxy_cli_args(args: argparse.Namespace) -> List[str]:
    out: List[str] = []
    if args.fit_proxy_max_range_exp is not None:
        out.extend(["--fit-proxy-max-range-exp", str(float(args.fit_proxy_max_range_exp))])
    if args.fit_proxy_max_azimuth_power is not None:
        out.extend(["--fit-proxy-max-azimuth-power", str(float(args.fit_proxy_max_azimuth_power))])
    if args.fit_proxy_min_weight is not None:
        out.extend(["--fit-proxy-min-weight", str(float(args.fit_proxy_min_weight))])
    if args.fit_proxy_max_weight is not None:
        out.extend(["--fit-proxy-max-weight", str(float(args.fit_proxy_max_weight))])
    return out


def _fit_proxy_policy_obj(args: argparse.Namespace) -> Optional[Dict[str, float]]:
    out: Dict[str, float] = {}
    if args.fit_proxy_max_range_exp is not None:
        out["max_range_power_exponent"] = float(args.fit_proxy_max_range_exp)
    if args.fit_proxy_max_azimuth_power is not None:
        out["max_azimuth_power"] = float(args.fit_proxy_max_azimuth_power)
    if args.fit_proxy_min_weight is not None:
        out["min_weight"] = float(args.fit_proxy_min_weight)
    if args.fit_proxy_max_weight is not None:
        out["max_weight"] = float(args.fit_proxy_max_weight)
    return out if out else None


def _build_fit_aware_pack(
    repo_root: Path,
    env: Mapping[str, str],
    source_pack_root: Path,
    fit_json: Path,
    output_pack_root: Path,
    reference_anchor: str,
    fit_proxy_cli_args: Sequence[str],
) -> Dict[str, Any]:
    summary_json = output_pack_root / "fit_aware_pack_summary.json"
    cmd = [
        "python3",
        "scripts/build_fit_aware_pack_from_existing_pack.py",
        "--source-pack-root",
        str(source_pack_root),
        "--output-pack-root",
        str(output_pack_root),
        "--path-power-fit-json",
        str(fit_json),
        "--reference-anchor",
        str(reference_anchor),
        "--output-summary-json",
        str(summary_json),
    ]
    cmd.extend(list(fit_proxy_cli_args))
    proc = _run(cmd, cwd=repo_root, env=env)
    if proc.returncode != 0:
        raise RuntimeError(
            "fit-aware pack build failed:\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return _load_json(summary_json)


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    out_root = Path(args.output_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    cp_summary_path = Path(args.case_partitioned_summary_json).expanduser().resolve()
    if not cp_summary_path.exists() or not cp_summary_path.is_file():
        raise FileNotFoundError(f"case partitioned summary not found: {cp_summary_path}")
    cp_summary = _load_json(cp_summary_path)

    final = cp_summary.get("final", {})
    if not isinstance(final, Mapping):
        raise ValueError("invalid case partitioned summary: missing final object")
    selected_by_family = final.get("selected_fit_by_family", {})
    if not isinstance(selected_by_family, Mapping):
        raise ValueError("invalid case partitioned summary: final.selected_fit_by_family")
    case_family_map = cp_summary.get("case_family_map", {})
    if not isinstance(case_family_map, Mapping):
        raise ValueError("invalid case partitioned summary: case_family_map")

    case_specs = [_parse_case_spec(x) for x in args.case]
    case_by_label = {str(x["label"]): x for x in case_specs}
    for label in case_by_label:
        if label not in case_family_map:
            raise ValueError(f"case label missing in case_family_map: {label}")

    fit_proxy_cli_args = _build_fit_proxy_cli_args(args)
    fit_proxy_policy = _fit_proxy_policy_obj(args)

    materialized_packs_root = out_root / "materialized_packs"
    materialized_packs_root.mkdir(parents=True, exist_ok=True)

    case_rows: List[Dict[str, Any]] = []
    plan_packs: List[Dict[str, Any]] = []

    for i, label in enumerate(sorted(case_by_label.keys())):
        spec = case_by_label[label]
        source_pack_root = Path(spec["source_pack_root"]).expanduser().resolve()
        if not source_pack_root.exists() or not source_pack_root.is_dir():
            raise FileNotFoundError(f"source pack root not found: {source_pack_root}")

        family = str(case_family_map[label])
        selected_fit = selected_by_family.get(family, None)
        fit_json = None if selected_fit is None else Path(str(selected_fit)).expanduser().resolve()
        if fit_json is not None and (not fit_json.exists() or not fit_json.is_file()):
            raise FileNotFoundError(f"selected fit json not found for family '{family}': {fit_json}")

        if fit_json is None:
            resolved_pack_root = source_pack_root
            materialization_mode = "baseline_source_pack"
            fit_pack_summary_json = None
        else:
            resolved_pack_root = materialized_packs_root / f"pack_{i:02d}_{_safe_name(label)}_fitaware"
            _build_fit_aware_pack(
                repo_root=repo_root,
                env=env,
                source_pack_root=source_pack_root,
                fit_json=fit_json,
                output_pack_root=resolved_pack_root,
                reference_anchor=str(args.reference_anchor),
                fit_proxy_cli_args=fit_proxy_cli_args,
            )
            materialization_mode = "fit_aware_rebuilt_pack"
            fit_pack_summary_json = str(resolved_pack_root / "fit_aware_pack_summary.json")

        replay_manifest_json = resolved_pack_root / "replay_manifest.json"
        if not replay_manifest_json.exists() or not replay_manifest_json.is_file():
            raise FileNotFoundError(f"replay manifest missing at resolved pack: {replay_manifest_json}")

        lock_policy = _load_lock_policy(resolved_pack_root)
        pack_id = str(label)
        plan_row: Dict[str, Any] = {
            "pack_id": pack_id,
            "replay_manifest_json": str(replay_manifest_json),
            "output_subdir": _safe_name(pack_id),
        }
        if lock_policy is not None:
            plan_row["lock_policy"] = lock_policy
        plan_packs.append(plan_row)

        baseline_replay_report_json = (
            Path(spec["baseline_replay_report_json"]).expanduser().resolve()
            if str(spec["baseline_replay_report_json"]).strip() != ""
            else _auto_baseline_replay_report(source_pack_root)
        )
        case_rows.append(
            {
                "case_index": int(i),
                "label": str(label),
                "family": family,
                "source_pack_root": str(source_pack_root),
                "materialization_mode": materialization_mode,
                "selected_fit_json": None if fit_json is None else str(fit_json),
                "fit_aware_pack_summary_json": fit_pack_summary_json,
                "resolved_pack_root": str(resolved_pack_root),
                "replay_manifest_json": str(replay_manifest_json),
                "baseline_replay_report_json": str(baseline_replay_report_json),
            }
        )

    case_manifest = {
        "version": 1,
        "source_case_partitioned_summary_json": str(cp_summary_path),
        "strategy": str(final.get("strategy", "")),
        "selection_mode": str(final.get("selection_mode", "")),
        "reference_anchor": str(args.reference_anchor),
        "fit_proxy_policy": fit_proxy_policy,
        "case_count": int(len(case_rows)),
        "cases": case_rows,
    }
    case_manifest_json = out_root / "case_level_lock_manifest.json"
    _save_json(case_manifest_json, case_manifest)

    measured_plan = {
        "version": 1,
        "packs": plan_packs,
        "metadata": {
            "generated_by": "run_case_partitioned_lock_manifest_replay.py",
            "source_case_partitioned_summary_json": str(cp_summary_path),
            "case_level_lock_manifest_json": str(case_manifest_json),
            "strategy": str(final.get("strategy", "")),
        },
    }
    measured_plan_json = out_root / "measured_replay_plan_case_partitioned.json"
    _save_json(measured_plan_json, measured_plan)

    measured_out_root = out_root / "measured_replay_outputs"
    replay_summary = run_measured_replay_plan(
        packs=plan_packs,
        output_root=str(measured_out_root),
        default_lock_policy={
            "min_pass_rate": float(args.default_min_pass_rate),
            "max_case_fail_count": int(args.default_max_case_fail_count),
            "require_motion_defaults_enabled": bool(
                args.default_require_motion_defaults_enabled
            ),
        },
    )
    measured_summary_json = out_root / "measured_replay_summary_case_partitioned.json"
    save_measured_replay_summary_json(str(measured_summary_json), replay_summary)

    replay_pack_by_id: Dict[str, Mapping[str, Any]] = {}
    for row in replay_summary.get("packs", []):
        if isinstance(row, Mapping):
            replay_pack_by_id[str(row.get("pack_id", ""))] = row

    improved = 0
    degraded = 0
    unchanged = 0
    missing_baseline = 0
    merged_case_rows: List[Dict[str, Any]] = []
    for row in case_rows:
        label = str(row["label"])
        replay_pack = replay_pack_by_id.get(label, {})
        replay_report_json = Path(str(replay_pack.get("replay_report_json", "")))
        new_summary = None
        if replay_report_json.exists() and replay_report_json.is_file():
            new_summary = _summary_from_replay_report(_load_json(replay_report_json))

        baseline_path = Path(str(row["baseline_replay_report_json"]))
        baseline_summary = None
        delta = None
        trend = "unknown"
        if baseline_path.exists() and baseline_path.is_file() and new_summary is not None:
            baseline_summary = _summary_from_replay_report(_load_json(baseline_path))
            delta = {
                "pass_count_delta": float(new_summary["pass_count"] - baseline_summary["pass_count"]),
                "fail_count_delta": float(new_summary["fail_count"] - baseline_summary["fail_count"]),
                "pass_rate_delta": float(new_summary["pass_rate"] - baseline_summary["pass_rate"]),
            }
            if delta["pass_count_delta"] > 0.0 or (
                delta["pass_count_delta"] == 0.0 and delta["pass_rate_delta"] > 0.0
            ):
                trend = "improved"
                improved += 1
            elif delta["pass_count_delta"] < 0.0 or (
                delta["pass_count_delta"] == 0.0 and delta["pass_rate_delta"] < 0.0
            ):
                trend = "degraded"
                degraded += 1
            else:
                trend = "unchanged"
                unchanged += 1
        else:
            missing_baseline += 1

        merged = dict(row)
        merged["replay_report_json"] = str(replay_report_json) if replay_report_json else None
        merged["new_replay_summary"] = new_summary
        merged["baseline_replay_summary"] = baseline_summary
        merged["delta_vs_baseline"] = delta
        merged["baseline_trend"] = trend
        merged_case_rows.append(merged)

    out = {
        "version": 1,
        "source_case_partitioned_summary_json": str(cp_summary_path),
        "case_level_lock_manifest_json": str(case_manifest_json),
        "measured_replay_plan_json": str(measured_plan_json),
        "measured_replay_summary_json": str(measured_summary_json),
        "strategy": str(final.get("strategy", "")),
        "selection_mode": str(final.get("selection_mode", "")),
        "case_count": int(len(case_rows)),
        "baseline_comparison": {
            "improved_case_count": int(improved),
            "degraded_case_count": int(degraded),
            "unchanged_case_count": int(unchanged),
            "missing_baseline_case_count": int(missing_baseline),
        },
        "replay_overall_lock_pass": bool(replay_summary.get("overall_lock_pass", False)),
        "cases": merged_case_rows,
    }
    out_summary_json = (
        out_root / "case_partitioned_lock_manifest_replay_summary.json"
        if args.output_summary_json is None
        else Path(args.output_summary_json).expanduser().resolve()
    )
    _save_json(out_summary_json, out)

    print("Case-partitioned lock manifest + replay verification completed.")
    print(f"  case_count: {out['case_count']}")
    print(f"  strategy: {out['strategy']}")
    print(f"  replay_overall_lock_pass: {out['replay_overall_lock_pass']}")
    print(f"  output_summary_json: {out_summary_json}")

    if (not out["replay_overall_lock_pass"]) and (not args.allow_unlocked):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
