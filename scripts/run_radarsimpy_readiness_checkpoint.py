#!/usr/bin/env python3
"""Run RadarSimPy readiness checkpoint and emit a single status report."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple


DEFAULT_TRIAL_PACKAGE_ROOT = "external/radarsimpy_trial/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU"
DEFAULT_LIBCOMPAT_DIR = "external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run RadarSimPy readiness checkpoint using smoke gate + wrapper gate + "
            "progress snapshot aggregation."
        )
    )
    p.add_argument("--reports-root", default="docs/reports")
    p.add_argument("--run-id", default="")
    p.add_argument("--output-json", default="")
    p.add_argument("--python-bin", default="")
    p.add_argument("--with-real-runtime", action="store_true")
    p.add_argument("--run-runtime-migration", action="store_true")
    p.add_argument("--require-real-e2e", action="store_true")
    p.add_argument("--e2e-rollup-json", default="")
    p.add_argument("--trial-package-root", default=DEFAULT_TRIAL_PACKAGE_ROOT)
    p.add_argument("--libcompat-dir", default=DEFAULT_LIBCOMPAT_DIR)
    p.add_argument("--allow-blocked", action="store_true")
    return p.parse_args()


def _resolve_python_bin(raw: str, repo_root: Path) -> str:
    text = str(raw).strip()
    if text != "":
        p = Path(text).expanduser()
        if p.exists():
            if p.is_absolute():
                return str(p)
            return str((repo_root / p))
        return text

    for candidate in (
        repo_root / ".venv" / "bin" / "python",
        repo_root / ".venv-po-sbr" / "bin" / "python",
    ):
        if candidate.exists():
            return str(candidate)
    return str(sys.executable)


def _resolve_path(raw: str, repo_root: Path) -> Path:
    p = Path(str(raw)).expanduser()
    if not p.is_absolute():
        p = (repo_root / p).resolve()
    else:
        p = p.resolve()
    return p


def _git(repo_root: Path, args: List[str]) -> Tuple[bool, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return False, proc.stderr.strip()
    return True, proc.stdout.strip()


def _run_cmd(cmd: List[str], cwd: Path, env: Mapping[str, str]) -> Dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=dict(env),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "cmd": list(cmd),
        "returncode": int(proc.returncode),
        "pass": bool(proc.returncode == 0),
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-80:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-80:]),
    }


def _load_json_if_exists(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists() or (not path.is_file()):
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    return payload


def _find_stage_ready(progress_payload: Mapping[str, Any], name: str) -> Optional[bool]:
    rows = progress_payload.get("stages")
    if not isinstance(rows, list):
        return None
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("name", "")) != str(name):
            continue
        return bool(row.get("ready", False))
    return None


def _extract_step_names(payload: Mapping[str, Any]) -> List[str]:
    rows = payload.get("steps")
    if not isinstance(rows, list):
        return []
    out: List[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        name = str(row.get("name", "")).strip()
        if name == "":
            continue
        out.append(name)
    return out


def main() -> None:
    args = parse_args()
    repo_root = Path.cwd().resolve()

    reports_root = _resolve_path(str(args.reports_root), repo_root=repo_root)
    reports_root.mkdir(parents=True, exist_ok=True)

    ok_head, head_short = _git(repo_root, ["rev-parse", "--short", "HEAD"])
    run_id = str(args.run_id).strip()
    if run_id == "":
        stamp = datetime.now(timezone.utc).strftime("%Y_%m_%d")
        head = head_short if ok_head else "unknown"
        run_id = f"{stamp}_{head}"

    output_json = str(args.output_json).strip()
    if output_json == "":
        output_path = reports_root / f"radarsimpy_readiness_checkpoint_{run_id}.json"
    else:
        output_path = _resolve_path(output_json, repo_root=repo_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    py_bin = _resolve_python_bin(args.python_bin, repo_root=repo_root)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"src{os.pathsep}{env['PYTHONPATH']}" if "PYTHONPATH" in env else "src"

    smoke_json = reports_root / f"radarsimpy_integration_smoke_gate_checkpoint_{run_id}.json"
    wrapper_json = reports_root / f"radarsimpy_wrapper_integration_gate_checkpoint_{run_id}.json"
    migration_root = reports_root / f"radarsimpy_migration_stepwise_checkpoint_{run_id}"
    migration_summary = migration_root / "summary.json"
    function_summary = reports_root / f"radarsimpy_function_progress_checkpoint_{run_id}.json"
    progress_json = reports_root / f"radarsimpy_progress_snapshot_{run_id}.json"

    smoke_cmd = [
        py_bin,
        "scripts/run_radarsimpy_integration_smoke_gate.py",
        "--output-summary-json",
        str(smoke_json),
        "--skip-readiness-runner-validator",
    ]
    smoke_skip_flag_requested = bool("--skip-readiness-runner-validator" in smoke_cmd)
    if bool(args.with_real_runtime):
        smoke_cmd.extend(
            [
                "--with-real-runtime",
                "--trial-package-root",
                str(args.trial_package_root),
                "--libcompat-dir",
                str(args.libcompat_dir),
            ]
        )
    smoke = _run_cmd(smoke_cmd, cwd=repo_root, env=env)
    smoke_payload = _load_json_if_exists(smoke_json) or {}
    smoke_step_names = _extract_step_names(smoke_payload)
    smoke_recursion_guard_active = bool(
        bool(smoke_payload.get("pass", False))
        and ("validate_run_radarsimpy_readiness_checkpoint" not in smoke_step_names)
    )

    wrapper_cmd = [
        py_bin,
        "scripts/run_radarsimpy_wrapper_integration_gate.py",
        "--output-summary-json",
        str(wrapper_json),
    ]
    if bool(args.with_real_runtime):
        wrapper_cmd.extend(
            [
                "--with-real-runtime",
                "--trial-package-root",
                str(args.trial_package_root),
                "--libcompat-dir",
                str(args.libcompat_dir),
            ]
        )
    wrapper = _run_cmd(wrapper_cmd, cwd=repo_root, env=env)
    wrapper_payload = _load_json_if_exists(wrapper_json) or {}

    migration: Optional[Dict[str, Any]] = None
    migration_payload: Dict[str, Any] = {}
    if bool(args.run_runtime_migration):
        migration_cmd = [
            py_bin,
            "scripts/run_radarsimpy_migration_stepwise.py",
            "--output-root",
            str(migration_root),
            "--output-summary-json",
            str(migration_summary),
            "--n-chirps",
            "6",
            "--samples-per-chirp",
            "512",
            "--runtime-failure-policy",
            "error",
            "--require-runtime-provider-mode",
            "--require-radarsimpy-simulation-used",
            "--trial-free-tier-geometry",
        ]
        migration = _run_cmd(migration_cmd, cwd=repo_root, env=env)
        migration_payload = _load_json_if_exists(migration_summary) or {}

    function_cmd = [
        py_bin,
        "scripts/show_radarsimpy_function_progress.py",
        "--repo-root",
        str(repo_root),
        "--output-json",
        str(function_summary),
    ]
    function_progress = _run_cmd(function_cmd, cwd=repo_root, env=env)
    function_payload = _load_json_if_exists(function_summary) or {}

    progress_cmd = [
        py_bin,
        "scripts/show_radarsimpy_progress.py",
        "--reports-root",
        str(reports_root),
        "--smoke-summary-json",
        str(smoke_json),
        "--wrapper-summary-json",
        str(wrapper_json),
        "--function-summary-json",
        str(function_summary),
        "--output-json",
        str(progress_json),
    ]
    if bool(args.run_runtime_migration):
        progress_cmd.extend(["--migration-summary-json", str(migration_summary)])
    if bool(args.require_real_e2e):
        e2e_rollup = str(args.e2e_rollup_json).strip()
        if e2e_rollup == "":
            progress_cmd.append("--strict-ready")
        else:
            progress_cmd.extend(["--e2e-rollup-json", str(_resolve_path(e2e_rollup, repo_root=repo_root))])
            progress_cmd.append("--strict-ready")
    progress = _run_cmd(progress_cmd, cwd=repo_root, env=env)
    progress_payload = _load_json_if_exists(progress_json) or {}

    smoke_pass = bool(smoke_payload.get("pass", False)) and bool(smoke.get("pass", False))
    wrapper_pass = bool(wrapper_payload.get("pass", False)) and bool(wrapper.get("pass", False))
    integration_stage_ready = _find_stage_ready(progress_payload, "integration_smoke_gate")
    wrapper_stage_ready = _find_stage_ready(progress_payload, "wrapper_integration_gate")
    function_stage_ready = _find_stage_ready(progress_payload, "function_api_coverage")
    migration_stage_ready = _find_stage_ready(progress_payload, "migration_stepwise")
    e2e_stage_ready = _find_stage_ready(progress_payload, "real_e2e")

    checks = {
        "smoke_gate_pass": smoke_pass,
        "smoke_skip_flag_applied": smoke_skip_flag_requested,
        "smoke_recursion_guard_active": smoke_recursion_guard_active,
        "wrapper_gate_pass": wrapper_pass,
        "progress_snapshot_generated": bool(progress_payload),
        "progress_integration_stage_ready": bool(integration_stage_ready is True),
        "progress_wrapper_stage_ready": bool(wrapper_stage_ready is True),
        "function_api_stage_ready": bool(function_stage_ready is True),
        "migration_stage_ready": bool(True if not args.run_runtime_migration else (migration_stage_ready is True)),
        "real_e2e_stage_ready": bool(True if not args.require_real_e2e else (e2e_stage_ready is True)),
    }

    ready = all(bool(v) for v in checks.values())
    status = "ready" if ready else "blocked"

    ok_branch, branch = _git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"])
    ok_head_full, head_commit = _git(repo_root, ["rev-parse", "HEAD"])

    report: Dict[str, Any] = {
        "version": 1,
        "report_name": "radarsimpy_readiness_checkpoint",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(repo_root),
        "run_id": run_id,
        "branch": branch if ok_branch else "",
        "head_commit": head_commit if ok_head_full else "",
        "with_real_runtime": bool(args.with_real_runtime),
        "run_runtime_migration": bool(args.run_runtime_migration),
        "require_real_e2e": bool(args.require_real_e2e),
        "smoke_gate_summary_json": str(smoke_json.resolve()),
        "wrapper_gate_summary_json": str(wrapper_json.resolve()),
        "migration_summary_json": str(migration_summary.resolve()) if args.run_runtime_migration else "",
        "function_summary_json": str(function_summary.resolve()),
        "progress_snapshot_json": str(progress_json.resolve()),
        "smoke_gate_status": "ready" if smoke_pass else "blocked",
        "wrapper_gate_status": "ready" if wrapper_pass else "blocked",
        "migration_status": _status_str(migration_payload.get("migration_status", "")),
        "function_status": "ready" if bool(function_payload.get("ready", False)) else "blocked",
        "smoke_gate_step_count": int(len(smoke_step_names)),
        "smoke_contains_readiness_runner_validator": bool(
            "validate_run_radarsimpy_readiness_checkpoint" in smoke_step_names
        ),
        "smoke_skip_readiness_runner_validator_requested": smoke_skip_flag_requested,
        "progress_overall_ready": bool(progress_payload.get("overall_ready", False)),
        "checkpoint_checks": checks,
        "overall_status": status,
        "commands": {
            "smoke_gate": smoke,
            "wrapper_gate": wrapper,
            "migration_stepwise": migration if migration is not None else {"skipped": True},
            "function_progress": function_progress,
            "progress_snapshot": progress,
        },
    }

    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("RadarSimPy readiness checkpoint completed.")
    print(f"  overall_status: {status}")
    print(f"  smoke_gate_status: {report['smoke_gate_status']}")
    print(f"  wrapper_gate_status: {report['wrapper_gate_status']}")
    print(f"  migration_status: {report['migration_status'] or 'skipped'}")
    print(f"  function_status: {report['function_status']}")
    print(f"  progress_overall_ready: {report['progress_overall_ready']}")
    print(f"  output_json: {output_path}")

    if (not ready) and (not bool(args.allow_blocked)):
        sys.exit(2)
    sys.exit(0)


def _status_str(v: Any) -> str:
    return str(v).strip()


if __name__ == "__main__":
    main()
