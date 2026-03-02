#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run consolidated RadarSimPy integration smoke gate "
            "(API coverage + wrapper + migration + periodic lock validators)."
        )
    )
    p.add_argument("--output-summary-json", required=True)
    p.add_argument(
        "--python-bin",
        default=None,
        help="Python interpreter to use for child scripts (default: current interpreter)",
    )
    p.add_argument(
        "--with-real-runtime",
        action="store_true",
        help="Also run wrapper integration gate in real-runtime mode",
    )
    p.add_argument(
        "--trial-package-root",
        default=None,
        help="Optional radarsimpy trial package root (used with --with-real-runtime)",
    )
    p.add_argument(
        "--libcompat-dir",
        default=None,
        help="Optional radarsimpy libcompat directory (used with --with-real-runtime)",
    )
    p.add_argument(
        "--allow-failures",
        action="store_true",
        help="Return 0 even when one or more steps fail",
    )
    return p.parse_args()


def _resolve_python_bin(raw: str | None) -> str:
    if raw is None:
        return str(sys.executable)
    p = Path(str(raw)).expanduser()
    if p.exists():
        if p.is_absolute():
            return str(p)
        return str((Path.cwd() / p))
    return str(raw)


def _run_step(
    *,
    name: str,
    cmd: List[str],
    cwd: Path,
    env: Dict[str, str],
) -> Dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "name": str(name),
        "cmd": list(cmd),
        "returncode": int(proc.returncode),
        "pass": bool(proc.returncode == 0),
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-80:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-80:]),
    }


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    output_summary_json = Path(args.output_summary_json).expanduser().resolve()
    output_summary_json.parent.mkdir(parents=True, exist_ok=True)

    py_bin = _resolve_python_bin(args.python_bin)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"src{os.pathsep}{env['PYTHONPATH']}" if "PYTHONPATH" in env else "src"

    steps_spec: List[Dict[str, Any]] = [
        {
            "name": "validate_radarsimpy_api_coverage_excluding_sim_lidar",
            "cmd": [py_bin, "scripts/validate_radarsimpy_api_coverage_excluding_sim_lidar.py"],
        },
        {
            "name": "validate_run_radarsimpy_wrapper_integration_gate",
            "cmd": [py_bin, "scripts/validate_run_radarsimpy_wrapper_integration_gate.py"],
        },
        {
            "name": "validate_run_radarsimpy_migration_stepwise",
            "cmd": [py_bin, "scripts/validate_run_radarsimpy_migration_stepwise.py"],
        },
        {
            "name": "validate_run_radarsimpy_periodic_parity_lock",
            "cmd": [py_bin, "scripts/validate_run_radarsimpy_periodic_parity_lock.py"],
        },
        {
            "name": "validate_build_radarsimpy_periodic_manifest_from_migration",
            "cmd": [py_bin, "scripts/validate_build_radarsimpy_periodic_manifest_from_migration.py"],
        },
    ]

    if bool(args.with_real_runtime):
        cmd = [
            py_bin,
            "scripts/run_radarsimpy_wrapper_integration_gate.py",
            "--with-real-runtime",
            "--output-summary-json",
            str(output_summary_json.parent / "radarsimpy_wrapper_integration_gate_real_from_smoke.json"),
        ]
        if args.trial_package_root is not None:
            cmd.extend(["--trial-package-root", str(args.trial_package_root)])
        if args.libcompat_dir is not None:
            cmd.extend(["--libcompat-dir", str(args.libcompat_dir)])
        steps_spec.append(
            {
                "name": "run_radarsimpy_wrapper_integration_gate_real_runtime",
                "cmd": cmd,
            }
        )

    steps: List[Dict[str, Any]] = []
    for row in steps_spec:
        steps.append(
            _run_step(
                name=str(row["name"]),
                cmd=list(row["cmd"]),
                cwd=repo_root,
                env=env,
            )
        )

    pass_count = int(sum(1 for row in steps if bool(row.get("pass", False))))
    fail_count = int(len(steps) - pass_count)
    gate_pass = bool(fail_count == 0)

    summary = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "python_bin": str(py_bin),
        "with_real_runtime": bool(args.with_real_runtime),
        "step_count": int(len(steps)),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass": gate_pass,
        "steps": steps,
    }
    output_summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("RadarSimPy integration smoke gate completed.")
    print(f"  pass: {gate_pass}")
    print(f"  pass_count: {pass_count}")
    print(f"  fail_count: {fail_count}")
    print(f"  output_summary_json: {output_summary_json}")

    if (not gate_pass) and (not bool(args.allow_failures)):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
