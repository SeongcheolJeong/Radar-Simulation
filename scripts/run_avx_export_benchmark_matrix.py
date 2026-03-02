#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


DEFAULT_CANDIDATE_BACKEND = "po_sbr_rt"
DEFAULT_REFERENCE_BACKEND = "sionna_rt"
DEFAULT_TRUTH_BACKEND = "analytic_targets"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run AVX export benchmark across scenario-matrix profile folders and emit one "
            "aggregate summary report."
        )
    )
    p.add_argument("--matrix-root", required=True, help="Root containing <profile>/golden_outputs/<backend>/pipeline_outputs")
    p.add_argument("--output-root", required=True, help="Directory for per-profile benchmark JSON outputs")
    p.add_argument("--output-summary-json", required=True, help="Matrix summary JSON output path")
    p.add_argument(
        "--profile",
        action="append",
        default=[],
        help="Profile id to include (repeatable, comma-separated). Default: all matrix-root subdirs.",
    )
    p.add_argument("--candidate-backend", default=DEFAULT_CANDIDATE_BACKEND, help="Candidate backend folder name")
    p.add_argument("--reference-backend", default=DEFAULT_REFERENCE_BACKEND, help="Reference backend folder name")
    p.add_argument("--truth-backend", default=DEFAULT_TRUTH_BACKEND, help="Truth backend folder name")
    p.add_argument("--python-bin", default=str(sys.executable), help="Python interpreter for child benchmark runs")

    p.add_argument(
        "--auto-tune-candidate-vs-truth",
        action="store_true",
        help="Pass through auto-tune mode to run_avx_export_benchmark.py",
    )
    p.add_argument("--auto-tune-range-shift-min", type=int, default=-2)
    p.add_argument("--auto-tune-range-shift-max", type=int, default=2)
    p.add_argument("--auto-tune-doppler-shift-min", type=int, default=-2)
    p.add_argument("--auto-tune-doppler-shift-max", type=int, default=2)
    p.add_argument("--auto-tune-angle-shift-min", type=int, default=-2)
    p.add_argument("--auto-tune-angle-shift-max", type=int, default=2)
    p.add_argument("--auto-tune-gain-db-min", type=float, default=-3.0)
    p.add_argument("--auto-tune-gain-db-max", type=float, default=3.0)
    p.add_argument("--auto-tune-gain-db-step", type=float, default=1.0)
    p.add_argument("--auto-tune-truth-mix-min", type=float, default=0.0)
    p.add_argument("--auto-tune-truth-mix-max", type=float, default=0.0)
    p.add_argument("--auto-tune-truth-mix-step", type=float, default=0.25)
    p.add_argument(
        "--strict-all-ready",
        action="store_true",
        help="Exit non-zero unless every row comparison_status is ready",
    )
    p.add_argument(
        "--strict-no-physics-worse",
        action="store_true",
        help="Exit non-zero if any row physics claim is candidate_worse_vs_truth",
    )
    return p.parse_args()


def _resolve_path(raw: str, cwd: Path, resolve_symlinks: bool = True) -> Path:
    p = Path(str(raw).strip()).expanduser()
    if not p.is_absolute():
        p = cwd / p
    if resolve_symlinks:
        return p.resolve()
    return p.absolute()


def _resolve_python_bin(raw: str, cwd: Path) -> str:
    text = str(raw).strip()
    if text == "":
        raise ValueError("python-bin must be non-empty")

    # Path-like values are resolved against cwd; command names use PATH lookup.
    if "/" in text or "\\" in text:
        path = Path(text).expanduser()
        if not path.is_absolute():
            # Preserve venv launcher path (symlink) to avoid collapsing to
            # system python executable without project dependencies.
            path = (cwd / path).absolute()
        else:
            path = path.absolute()
        if not path.exists():
            raise FileNotFoundError(f"python interpreter not found: {path}")
        return str(path)

    found = shutil.which(text)
    if found is None:
        raise FileNotFoundError(f"python interpreter not found on PATH: {text}")
    return str(Path(found).absolute())


def _build_subprocess_env(cwd: Path) -> Dict[str, str]:
    env = dict(os.environ)
    src_path = str((cwd / "src").resolve())
    py_path = str(env.get("PYTHONPATH", "")).strip()
    if py_path == "":
        env["PYTHONPATH"] = src_path
        return env

    tokens = py_path.split(os.pathsep)
    if src_path not in tokens:
        env["PYTHONPATH"] = src_path + os.pathsep + py_path
    return env


def _parse_profiles(items: Sequence[str], matrix_root: Path) -> List[str]:
    if len(items) == 0:
        out = sorted([p.name for p in matrix_root.iterdir() if p.is_dir()])
        if len(out) == 0:
            raise ValueError(f"no profile directories found under matrix root: {matrix_root}")
        return out
    out: List[str] = []
    for raw in items:
        for token in str(raw).split(","):
            name = str(token).strip()
            if name == "":
                continue
            if name not in out:
                out.append(name)
    if len(out) == 0:
        raise ValueError("at least one profile must be selected")
    return out


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _file_if_exists(path: Path) -> Optional[Path]:
    return path if path.exists() else None


def _backend_artifacts(profile_root: Path, backend: str) -> Dict[str, Optional[Path]]:
    base = profile_root / "golden_outputs" / backend / "pipeline_outputs"
    return {
        "radar_map_npz": _file_if_exists(base / "radar_map.npz"),
        "path_list_json": _file_if_exists(base / "path_list.json"),
        "adc_cube_npz": _file_if_exists(base / "adc_cube.npz"),
    }


def _run_cmd(cmd: List[str], cwd: Path) -> Dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=_build_subprocess_env(cwd),
        capture_output=True,
        text=True,
    )
    return {
        "ok": bool(proc.returncode == 0),
        "return_code": int(proc.returncode),
        "stdout": str(proc.stdout).strip(),
        "stderr": str(proc.stderr).strip(),
        "cmd": cmd,
    }


def _build_benchmark_cmd(
    python_bin: str,
    output_json: Path,
    profile: str,
    candidate_label: str,
    reference_label: str,
    truth_label: str,
    candidate: Mapping[str, Optional[Path]],
    reference: Mapping[str, Optional[Path]],
    truth: Mapping[str, Optional[Path]],
    args: argparse.Namespace,
) -> List[str]:
    cand_radar = candidate.get("radar_map_npz")
    ref_radar = reference.get("radar_map_npz")
    truth_radar = truth.get("radar_map_npz")
    if cand_radar is None:
        raise FileNotFoundError(f"{profile}: missing candidate radar_map.npz")
    if ref_radar is None:
        raise FileNotFoundError(f"{profile}: missing reference radar_map.npz")
    if truth_radar is None:
        raise FileNotFoundError(f"{profile}: missing truth radar_map.npz")

    cmd = [
        python_bin,
        "scripts/run_avx_export_benchmark.py",
        "--candidate-label",
        candidate_label,
        "--reference-label",
        reference_label,
        "--truth-label",
        truth_label,
        "--candidate-radar-map-npz",
        str(cand_radar),
        "--reference-radar-map-npz",
        str(ref_radar),
        "--truth-radar-map-npz",
        str(truth_radar),
        "--output-json",
        str(output_json),
    ]

    cand_paths = candidate.get("path_list_json")
    ref_paths = reference.get("path_list_json")
    cand_adc = candidate.get("adc_cube_npz")
    ref_adc = reference.get("adc_cube_npz")
    if cand_paths is not None:
        cmd.extend(["--candidate-path-list-json", str(cand_paths)])
    if ref_paths is not None:
        cmd.extend(["--reference-path-list-json", str(ref_paths)])
    if cand_adc is not None:
        cmd.extend(["--candidate-adc-cube-npz", str(cand_adc)])
    if ref_adc is not None:
        cmd.extend(["--reference-adc-cube-npz", str(ref_adc)])

    if bool(args.auto_tune_candidate_vs_truth):
        cmd.extend(
            [
                "--auto-tune-candidate-vs-truth",
                "--auto-tune-range-shift-min",
                str(int(args.auto_tune_range_shift_min)),
                "--auto-tune-range-shift-max",
                str(int(args.auto_tune_range_shift_max)),
                "--auto-tune-doppler-shift-min",
                str(int(args.auto_tune_doppler_shift_min)),
                "--auto-tune-doppler-shift-max",
                str(int(args.auto_tune_doppler_shift_max)),
                "--auto-tune-angle-shift-min",
                str(int(args.auto_tune_angle_shift_min)),
                "--auto-tune-angle-shift-max",
                str(int(args.auto_tune_angle_shift_max)),
                "--auto-tune-gain-db-min",
                str(float(args.auto_tune_gain_db_min)),
                "--auto-tune-gain-db-max",
                str(float(args.auto_tune_gain_db_max)),
                "--auto-tune-gain-db-step",
                str(float(args.auto_tune_gain_db_step)),
                "--auto-tune-truth-mix-min",
                str(float(args.auto_tune_truth_mix_min)),
                "--auto-tune-truth-mix-max",
                str(float(args.auto_tune_truth_mix_max)),
                "--auto-tune-truth-mix-step",
                str(float(args.auto_tune_truth_mix_step)),
            ]
        )
    return cmd


def _row_from_report(profile: str, report_path: Path, run_step: Mapping[str, Any]) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "profile": profile,
        "report_json": str(report_path),
        "run_step": dict(run_step),
        "comparison_status": "blocked",
        "physics_claim": "inconclusive",
        "function_claim": "equivalent",
        "cand_fail": None,
        "ref_fail": None,
        "cand_score": None,
        "ref_score": None,
        "cand_fn_score": None,
        "ref_fn_score": None,
        "candidate_transform_mode": None,
    }
    if not bool(run_step.get("ok", False)):
        return row
    if not report_path.exists():
        row["run_step"] = dict(run_step)
        row["run_step"]["error"] = f"report_not_found:{report_path}"
        return row

    report = _load_json(report_path)
    summary = report.get("summary")
    if not isinstance(summary, Mapping):
        row["run_step"] = dict(run_step)
        row["run_step"]["error"] = "missing_summary"
        return row

    physics = report.get("physics") if isinstance(report.get("physics"), Mapping) else {}
    details = physics.get("better_than_reference_physics_details")
    if not isinstance(details, Mapping):
        details = {}
    function_usability = (
        report.get("function_usability") if isinstance(report.get("function_usability"), Mapping) else {}
    )
    candidate_fn = function_usability.get("candidate") if isinstance(function_usability.get("candidate"), Mapping) else {}
    reference_fn = function_usability.get("reference") if isinstance(function_usability.get("reference"), Mapping) else {}

    row["comparison_status"] = str(report.get("comparison_status", "blocked")).strip() or "blocked"
    row["physics_claim"] = str(physics.get("better_than_reference_physics_claim", "inconclusive")).strip() or "inconclusive"
    row["function_claim"] = str(
        function_usability.get("better_than_reference_function_usability_claim", "equivalent")
    ).strip() or "equivalent"
    row["cand_fail"] = int(details.get("candidate_fail_count", 0)) if "candidate_fail_count" in details else None
    row["ref_fail"] = int(details.get("reference_fail_count", 0)) if "reference_fail_count" in details else None
    row["cand_score"] = float(details.get("candidate_composite_score")) if "candidate_composite_score" in details else None
    row["ref_score"] = float(details.get("reference_composite_score")) if "reference_composite_score" in details else None
    row["cand_fn_score"] = float(candidate_fn.get("score")) if "score" in candidate_fn else None
    row["ref_fn_score"] = float(reference_fn.get("score")) if "score" in reference_fn else None
    row["candidate_transform_mode"] = str(summary.get("candidate_transform_mode", "")).strip() or None
    return row


def _aggregate_counts(rows: Sequence[Mapping[str, Any]]) -> Dict[str, int]:
    status_ready = 0
    physics_better = 0
    physics_equivalent = 0
    physics_worse = 0
    function_better = 0
    function_equivalent = 0
    function_worse = 0

    for row in rows:
        if str(row.get("comparison_status", "")) == "ready":
            status_ready += 1

        physics_claim = str(row.get("physics_claim", ""))
        if physics_claim == "candidate_better_vs_truth":
            physics_better += 1
        elif physics_claim == "candidate_worse_vs_truth":
            physics_worse += 1
        elif physics_claim == "equivalent_vs_truth":
            physics_equivalent += 1

        function_claim = str(row.get("function_claim", ""))
        if function_claim == "candidate_better":
            function_better += 1
        elif function_claim == "candidate_worse":
            function_worse += 1
        elif function_claim == "equivalent":
            function_equivalent += 1

    return {
        "total_profiles": int(len(rows)),
        "ready_count": int(status_ready),
        "physics_better_count": int(physics_better),
        "physics_equivalent_count": int(physics_equivalent),
        "physics_worse_count": int(physics_worse),
        "function_better_count": int(function_better),
        "function_equivalent_count": int(function_equivalent),
        "function_worse_count": int(function_worse),
    }


def main() -> None:
    args = parse_args()
    cwd = Path.cwd().resolve()

    matrix_root = _resolve_path(args.matrix_root, cwd=cwd)
    if not matrix_root.exists():
        raise FileNotFoundError(f"matrix root not found: {matrix_root}")
    output_root = _resolve_path(args.output_root, cwd=cwd)
    output_root.mkdir(parents=True, exist_ok=True)
    output_summary_json = _resolve_path(args.output_summary_json, cwd=cwd)
    output_summary_json.parent.mkdir(parents=True, exist_ok=True)
    python_bin = _resolve_python_bin(args.python_bin, cwd=cwd)

    profiles = _parse_profiles(args.profile, matrix_root=matrix_root)
    rows: List[Dict[str, Any]] = []

    for profile in profiles:
        profile_root = matrix_root / profile
        candidate_artifacts = _backend_artifacts(profile_root, backend=str(args.candidate_backend))
        reference_artifacts = _backend_artifacts(profile_root, backend=str(args.reference_backend))
        truth_artifacts = _backend_artifacts(profile_root, backend=str(args.truth_backend))

        profile_report_json = output_root / f"{profile}.json"
        cmd = _build_benchmark_cmd(
            python_bin=python_bin,
            output_json=profile_report_json,
            profile=profile,
            candidate_label=str(args.candidate_backend),
            reference_label=str(args.reference_backend),
            truth_label=str(args.truth_backend),
            candidate=candidate_artifacts,
            reference=reference_artifacts,
            truth=truth_artifacts,
            args=args,
        )
        run_step = _run_cmd(cmd=cmd, cwd=cwd)
        row = _row_from_report(profile=profile, report_path=profile_report_json, run_step=run_step)
        rows.append(row)

    counts = _aggregate_counts(rows)
    report = {
        "version": 1,
        "report_name": "avx_export_benchmark_matrix_summary",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "matrix_root": str(matrix_root),
        "output_root": str(output_root),
        "candidate_backend": str(args.candidate_backend),
        "reference_backend": str(args.reference_backend),
        "truth_backend": str(args.truth_backend),
        "auto_tune_candidate_vs_truth": bool(args.auto_tune_candidate_vs_truth),
        "rows": rows,
        "counts": counts,
    }
    output_summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("AVX export benchmark matrix completed.")
    print(f"  profiles: {len(rows)}")
    print(f"  ready_count: {counts['ready_count']}")
    print(f"  physics_better/equivalent/worse: {counts['physics_better_count']}/{counts['physics_equivalent_count']}/{counts['physics_worse_count']}")
    print(f"  function_better/equivalent/worse: {counts['function_better_count']}/{counts['function_equivalent_count']}/{counts['function_worse_count']}")
    print(f"  output_summary_json: {output_summary_json}")

    if bool(args.strict_all_ready) and counts["ready_count"] != counts["total_profiles"]:
        raise RuntimeError("strict all-ready failed")
    if bool(args.strict_no_physics_worse) and counts["physics_worse_count"] > 0:
        raise RuntimeError("strict no-physics-worse failed")


if __name__ == "__main__":
    main()
