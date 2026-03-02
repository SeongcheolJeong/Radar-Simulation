#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping


def _timestamp_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run RadarSimPy wrapper integration gate checks. "
            "By default this runs deterministic/stubbed validators only."
        )
    )
    p.add_argument(
        "--output-summary-json",
        default=f"docs/reports/radarsimpy_wrapper_integration_gate_{_timestamp_tag()}.json",
        help="Summary JSON output path.",
    )
    p.add_argument(
        "--with-real-runtime",
        action="store_true",
        help="Also run real RadarSimPy runtime probe and strict pilot.",
    )
    p.add_argument(
        "--trial-package-root",
        default=(
            "external/radarsimpy_trial/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU"
        ),
        help="RadarSimPy package root used when --with-real-runtime is set.",
    )
    p.add_argument(
        "--libcompat-dir",
        default="external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu",
        help="Shared library directory for RadarSimPy runtime.",
    )
    p.add_argument(
        "--allow-failures",
        action="store_true",
        help="Return 0 even when one or more checks fail.",
    )
    return p.parse_args()


def _run(
    cmd: List[str],
    repo_root: Path,
    env: Mapping[str, str],
) -> Dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        env=dict(env),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": bool(proc.returncode == 0),
        "return_code": int(proc.returncode),
        "cmd": cmd,
        "stdout": str(proc.stdout).strip(),
        "stderr": str(proc.stderr).strip(),
    }


def _build_base_env(repo_root: Path) -> Dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")
    return env


def _run_real_runtime_probe(
    repo_root: Path,
    env: Mapping[str, str],
) -> Dict[str, Any]:
    code = (
        "from avxsim import inspect_radarsimpy_api_coverage\n"
        "cov = inspect_radarsimpy_api_coverage()\n"
        "print(cov['all_supported_available'])\n"
        "print(cov['missing'])\n"
        "print(cov['excluded_api'])\n"
    )
    return _run([sys.executable, "-c", code], repo_root=repo_root, env=env)


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]

    summary_path = Path(args.output_summary_json).expanduser()
    if not summary_path.is_absolute():
        summary_path = (repo_root / summary_path).resolve()
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    env_base = _build_base_env(repo_root=repo_root)
    checks: List[Dict[str, Any]] = []

    deterministic_cmds = [
        (
            "wrapper_entrypoint_guard",
            [sys.executable, "scripts/validate_radarsimpy_wrapper_entrypoint_guard.py"],
        ),
        (
            "api_coverage_excluding_sim_lidar",
            [sys.executable, "scripts/validate_radarsimpy_api_coverage_excluding_sim_lidar.py"],
        ),
        (
            "runtime_provider_integration_stubbed",
            [sys.executable, "scripts/validate_scene_runtime_radarsimpy_provider_integration_stubbed.py"],
        ),
        (
            "periodic_parity_lock_runner",
            [sys.executable, "scripts/validate_run_radarsimpy_periodic_parity_lock.py"],
        ),
        (
            "runtime_pilot_runner",
            [sys.executable, "scripts/validate_run_scene_runtime_radarsimpy_pilot.py"],
        ),
        (
            "migration_stepwise_runner",
            [sys.executable, "scripts/validate_run_radarsimpy_migration_stepwise.py"],
        ),
    ]
    for name, cmd in deterministic_cmds:
        result = _run(cmd, repo_root=repo_root, env=env_base)
        result["check_name"] = name
        checks.append(result)

    real_runtime: Dict[str, Any] = {"requested": bool(args.with_real_runtime)}
    if args.with_real_runtime:
        trial_pkg_root = Path(args.trial_package_root).expanduser()
        if not trial_pkg_root.is_absolute():
            trial_pkg_root = (repo_root / trial_pkg_root).resolve()
        libcompat_dir = Path(args.libcompat_dir).expanduser()
        if not libcompat_dir.is_absolute():
            libcompat_dir = (repo_root / libcompat_dir).resolve()

        env_real = dict(env_base)
        env_real["PYTHONPATH"] = f"{env_base['PYTHONPATH']}:{trial_pkg_root}"
        env_real["LD_LIBRARY_PATH"] = f"{libcompat_dir}:{env_real.get('LD_LIBRARY_PATH', '')}"

        probe = _run_real_runtime_probe(repo_root=repo_root, env=env_real)
        probe["check_name"] = "real_runtime_api_probe"
        checks.append(probe)
        real_runtime["api_probe"] = probe
        real_runtime["trial_package_root"] = str(trial_pkg_root)
        real_runtime["libcompat_dir"] = str(libcompat_dir)

        pilot_output_root = (
            repo_root
            / "docs/reports"
            / f"radarsimpy_runtime_pilot_wrapper_gate_{_timestamp_tag()}"
        )
        pilot_summary = pilot_output_root / "summary.json"
        pilot_cmd = [
            sys.executable,
            "scripts/run_scene_runtime_radarsimpy_pilot.py",
            "--output-root",
            str(pilot_output_root),
            "--output-summary-json",
            str(pilot_summary),
            "--runtime-failure-policy",
            "error",
            "--simulation-mode",
            "radarsimpy_adc",
            "--require-real-simulation",
            "--trial-free-tier-geometry",
            "--runtime-device",
            "cpu",
        ]
        pilot_result = _run(pilot_cmd, repo_root=repo_root, env=env_real)
        pilot_result["check_name"] = "real_runtime_strict_pilot"
        checks.append(pilot_result)
        real_runtime["strict_pilot"] = pilot_result
        real_runtime["pilot_output_root"] = str(pilot_output_root)
        real_runtime["pilot_summary_json"] = str(pilot_summary)

    pass_count = int(sum(1 for item in checks if bool(item.get("ok"))))
    fail_count = int(len(checks) - pass_count)
    summary: Dict[str, Any] = {
        "version": 1,
        "gate": "radarsimpy_wrapper_integration",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "with_real_runtime": bool(args.with_real_runtime),
        "allow_failures": bool(args.allow_failures),
        "check_count": int(len(checks)),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass": bool(fail_count == 0),
        "checks": checks,
        "real_runtime": real_runtime,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("RadarSimPy wrapper integration gate completed.")
    print(f"  pass: {summary['pass']}")
    print(f"  pass_count: {summary['pass_count']}")
    print(f"  fail_count: {summary['fail_count']}")
    print(f"  output_summary_json: {summary_path}")

    if (not bool(summary["pass"])) and (not args.allow_failures):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
