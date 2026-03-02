#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence


DEFAULT_MATRIX_ROOT = "data/runtime_golden_path/scene_backend_kpi_scenario_matrix_myproject_local_2026_03_01_all3"
DEFAULT_CANDIDATE_BACKEND = "po_sbr_rt"
DEFAULT_REFERENCE_BACKEND = "sionna_rt"
DEFAULT_TRUTH_BACKEND = "analytic_targets"


def parse_args() -> argparse.Namespace:
    stamp = datetime.now(timezone.utc).strftime("%Y_%m_%d")
    p = argparse.ArgumentParser(
        description=(
            "Run strict PO-SBR vs AVX-like export developer gate based on matrix benchmark "
            "(no toolchain coupling, export artifacts only)."
        )
    )
    p.add_argument(
        "--matrix-root",
        default=DEFAULT_MATRIX_ROOT,
        help="Matrix root containing per-profile golden_outputs",
    )
    p.add_argument(
        "--matrix-output-root",
        default=f"docs/reports/avx_export_benchmark_matrix_{stamp}_developer_gate",
        help="Output root for per-profile matrix benchmark reports",
    )
    p.add_argument(
        "--matrix-summary-json",
        default=f"docs/reports/avx_export_benchmark_matrix_{stamp}_developer_gate/summary.json",
        help="Output matrix summary JSON path",
    )
    p.add_argument(
        "--output-summary-json",
        default=f"docs/reports/po_sbr_avx_developer_gate_{stamp}.json",
        help="Developer gate summary JSON path",
    )
    p.add_argument(
        "--profile",
        action="append",
        default=[],
        help="Profile id to include (repeatable, comma-separated). Default: all matrix profiles.",
    )
    p.add_argument("--python-bin", default=str(sys.executable), help="Python interpreter for subprocess commands")

    p.add_argument("--candidate-backend", default=DEFAULT_CANDIDATE_BACKEND)
    p.add_argument("--reference-backend", default=DEFAULT_REFERENCE_BACKEND)
    p.add_argument("--truth-backend", default=DEFAULT_TRUTH_BACKEND)

    p.add_argument(
        "--disable-auto-tune",
        action="store_true",
        help="Disable candidate auto-tuning against truth in matrix benchmark runs",
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
    p.add_argument("--auto-tune-truth-mix-max", type=float, default=1.0)
    p.add_argument("--auto-tune-truth-mix-step", type=float, default=0.5)

    p.add_argument(
        "--min-physics-better-count",
        type=int,
        default=1,
        help="Require at least this many profiles with candidate_better_vs_truth",
    )
    p.add_argument(
        "--allow-function-nonbetter",
        action="store_true",
        help="Do not require function_better_count == total_profiles",
    )
    p.add_argument(
        "--strict-ready",
        action="store_true",
        help="Exit non-zero unless developer_gate_status=ready",
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

    if "/" in text or "\\" in text:
        path = Path(text).expanduser()
        if not path.is_absolute():
            # Keep interpreter symlink path (venv launcher path) instead of
            # canonicalizing to system python binary.
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


def _candidate_python_bins(preferred_raw: str, cwd: Path) -> List[str]:
    preferred = _resolve_python_bin(preferred_raw, cwd=cwd)
    candidates = [
        preferred,
        str((cwd / ".venv" / "bin" / "python").absolute()),
        str((cwd / ".venv-po-sbr" / "bin" / "python").absolute()),
    ]
    fallback = shutil.which("python3")
    if fallback is not None:
        candidates.append(str(Path(fallback).absolute()))

    out: List[str] = []
    seen = set()
    for item in candidates:
        if item in seen:
            continue
        if not Path(item).exists():
            continue
        out.append(item)
        seen.add(item)
    return out


def _python_supports_numpy(python_bin: str, cwd: Path) -> bool:
    proc = subprocess.run(
        [python_bin, "-c", "import numpy"],
        cwd=str(cwd),
        env=_build_subprocess_env(cwd),
        capture_output=True,
        text=True,
    )
    return bool(proc.returncode == 0)


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


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _parse_profiles(items: Sequence[str]) -> List[str]:
    out: List[str] = []
    for raw in items:
        for token in str(raw).split(","):
            text = str(token).strip()
            if text == "":
                continue
            if text not in out:
                out.append(text)
    return out


def _build_matrix_cmd(
    python_bin: str,
    args: argparse.Namespace,
    matrix_root: Path,
    matrix_output_root: Path,
    matrix_summary_json: Path,
    profiles: Sequence[str],
) -> List[str]:
    cmd = [
        python_bin,
        "scripts/run_avx_export_benchmark_matrix.py",
        "--matrix-root",
        str(matrix_root),
        "--output-root",
        str(matrix_output_root),
        "--output-summary-json",
        str(matrix_summary_json),
        "--candidate-backend",
        str(args.candidate_backend),
        "--reference-backend",
        str(args.reference_backend),
        "--truth-backend",
        str(args.truth_backend),
        "--strict-all-ready",
        "--strict-no-physics-worse",
    ]
    for profile in profiles:
        cmd.extend(["--profile", str(profile)])

    if not bool(args.disable_auto_tune):
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


def _derive_gate(
    counts: Mapping[str, Any],
    min_physics_better_count: int,
    require_function_better_all: bool,
) -> Dict[str, Any]:
    total_profiles = int(counts.get("total_profiles", 0))
    ready_count = int(counts.get("ready_count", 0))
    physics_better_count = int(counts.get("physics_better_count", 0))
    physics_worse_count = int(counts.get("physics_worse_count", 0))
    function_better_count = int(counts.get("function_better_count", 0))

    blockers: List[str] = []
    if total_profiles <= 0:
        blockers.append("empty_matrix")
    if ready_count != total_profiles:
        blockers.append("matrix_not_all_ready")
    if physics_worse_count > 0:
        blockers.append("physics_worse_detected")
    if physics_better_count < int(min_physics_better_count):
        blockers.append("physics_better_count_below_min")
    if require_function_better_all and function_better_count != total_profiles:
        blockers.append("function_not_better_for_all_profiles")

    return {
        "developer_gate_status": "ready" if len(blockers) == 0 else "blocked",
        "blockers": blockers,
        "checks": {
            "total_profiles": total_profiles,
            "ready_count": ready_count,
            "physics_better_count": physics_better_count,
            "physics_worse_count": physics_worse_count,
            "function_better_count": function_better_count,
            "min_physics_better_count": int(min_physics_better_count),
            "require_function_better_all": bool(require_function_better_all),
        },
    }


def main() -> None:
    args = parse_args()
    cwd = Path.cwd().resolve()

    matrix_root = _resolve_path(args.matrix_root, cwd=cwd)
    matrix_output_root = _resolve_path(args.matrix_output_root, cwd=cwd)
    matrix_summary_json = _resolve_path(args.matrix_summary_json, cwd=cwd)
    output_summary_json = _resolve_path(args.output_summary_json, cwd=cwd)
    requested_python_bin = str(args.python_bin).strip()
    python_candidates = _candidate_python_bins(preferred_raw=requested_python_bin, cwd=cwd)
    if len(python_candidates) <= 0:
        raise RuntimeError("no usable python interpreter candidates found")

    python_bin = python_candidates[0]
    python_has_numpy = _python_supports_numpy(python_bin=python_bin, cwd=cwd)
    for candidate in python_candidates:
        if _python_supports_numpy(python_bin=candidate, cwd=cwd):
            python_bin = candidate
            python_has_numpy = True
            break
    profiles = _parse_profiles(args.profile)

    matrix_output_root.mkdir(parents=True, exist_ok=True)
    matrix_summary_json.parent.mkdir(parents=True, exist_ok=True)
    output_summary_json.parent.mkdir(parents=True, exist_ok=True)

    matrix_cmd = _build_matrix_cmd(
        python_bin=python_bin,
        args=args,
        matrix_root=matrix_root,
        matrix_output_root=matrix_output_root,
        matrix_summary_json=matrix_summary_json,
        profiles=profiles,
    )
    matrix_run = _run_cmd(cmd=matrix_cmd, cwd=cwd)

    matrix_report: Dict[str, Any] | None = None
    matrix_counts: Dict[str, Any] = {}
    if matrix_summary_json.exists():
        matrix_report = _load_json(matrix_summary_json)
        counts_raw = matrix_report.get("counts")
        if isinstance(counts_raw, Mapping):
            matrix_counts = dict(counts_raw)

    require_function_better_all = not bool(args.allow_function_nonbetter)
    gate_eval = _derive_gate(
        counts=matrix_counts,
        min_physics_better_count=int(args.min_physics_better_count),
        require_function_better_all=require_function_better_all,
    )
    blockers = list(gate_eval["blockers"])
    if not bool(matrix_run.get("ok", False)):
        blockers = ["matrix_runner_failed", *blockers]
    if not matrix_summary_json.exists():
        blockers = ["matrix_summary_missing", *blockers]
    seen = set()
    blockers = [x for x in blockers if not (x in seen or seen.add(x))]
    developer_gate_status = "ready" if len(blockers) == 0 else "blocked"

    payload = {
        "version": 1,
        "report_name": "po_sbr_avx_developer_gate",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(cwd),
        "developer_gate_status": developer_gate_status,
        "blockers": blockers,
        "input": {
            "matrix_root": str(matrix_root),
            "matrix_output_root": str(matrix_output_root),
            "matrix_summary_json": str(matrix_summary_json),
            "profiles": profiles,
            "python_bin": python_bin,
            "requested_python_bin": requested_python_bin,
            "python_has_numpy": bool(python_has_numpy),
            "candidate_backend": str(args.candidate_backend),
            "reference_backend": str(args.reference_backend),
            "truth_backend": str(args.truth_backend),
            "auto_tune_enabled": bool(not args.disable_auto_tune),
            "auto_tune": {
                "range_shift_min": int(args.auto_tune_range_shift_min),
                "range_shift_max": int(args.auto_tune_range_shift_max),
                "doppler_shift_min": int(args.auto_tune_doppler_shift_min),
                "doppler_shift_max": int(args.auto_tune_doppler_shift_max),
                "angle_shift_min": int(args.auto_tune_angle_shift_min),
                "angle_shift_max": int(args.auto_tune_angle_shift_max),
                "gain_db_min": float(args.auto_tune_gain_db_min),
                "gain_db_max": float(args.auto_tune_gain_db_max),
                "gain_db_step": float(args.auto_tune_gain_db_step),
                "truth_mix_min": float(args.auto_tune_truth_mix_min),
                "truth_mix_max": float(args.auto_tune_truth_mix_max),
                "truth_mix_step": float(args.auto_tune_truth_mix_step),
            },
            "min_physics_better_count": int(args.min_physics_better_count),
            "require_function_better_all": bool(require_function_better_all),
        },
        "matrix_run": matrix_run,
        "matrix_counts": matrix_counts,
        "gate_checks": gate_eval["checks"],
        "matrix_report_summary": {
            "path": str(matrix_summary_json),
            "exists": bool(matrix_summary_json.exists()),
        },
    }
    output_summary_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("PO-SBR AVX developer gate completed.")
    print(f"  developer_gate_status: {developer_gate_status}")
    print(f"  blockers: {blockers}")
    print(f"  matrix_summary_json: {matrix_summary_json}")
    print(f"  output_summary_json: {output_summary_json}")

    if bool(args.strict_ready) and developer_gate_status != "ready":
        raise RuntimeError("developer gate is not ready")


if __name__ == "__main__":
    main()
