#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_TRIAL_PACKAGE_ROOT = "external/radarsimpy_trial/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU"
DEFAULT_LIBCOMPAT_DIR = "external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu"
RADARSIMPY_LICENSE_FILE_ENV = "RADARSIMPY_LICENSE_FILE"
RADARSIMPY_PACKAGE_ROOT_ENV = "RADARSIMPY_PACKAGE_ROOT"
RADARSIMPY_LIBCOMPAT_DIR_ENV = "RADARSIMPY_LIBCOMPAT_DIR"


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
        help=(
            "Optional RadarSimPy package root (used with --with-real-runtime). "
            "In trial tier, omitted value auto-resolves to bundled trial package path."
        ),
    )
    p.add_argument(
        "--libcompat-dir",
        default=None,
        help=(
            "Optional RadarSimPy libcompat directory (used with --with-real-runtime). "
            "In trial tier, omitted value auto-resolves to bundled libcompat path."
        ),
    )
    p.add_argument(
        "--runtime-license-tier",
        choices=("trial", "production"),
        default="trial",
        help=(
            "Runtime license tier policy forwarded to wrapper integration gate in "
            "--with-real-runtime mode."
        ),
    )
    p.add_argument(
        "--license-file",
        default=None,
        help=(
            "Optional RadarSimPy license file path. "
            f"When provided, sets {RADARSIMPY_LICENSE_FILE_ENV} for real-runtime steps."
        ),
    )
    p.add_argument(
        "--allow-failures",
        action="store_true",
        help="Return 0 even when one or more steps fail",
    )
    p.add_argument(
        "--skip-readiness-runner-validator",
        action="store_true",
        help=(
            "Skip validate_run_radarsimpy_readiness_checkpoint to avoid recursive "
            "nesting when this smoke gate is executed from the readiness checkpoint runner."
        ),
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


def _stage_license_for_import_time_lookup(
    *,
    trial_package_root: str,
    license_file: str,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "requested": False,
        "staged": False,
        "method": "",
        "source_path": "",
        "staged_path": "",
        "cleanup_required": False,
        "error": "",
    }
    trial_root_text = str(trial_package_root).strip()
    license_text = str(license_file).strip()
    if trial_root_text == "" or license_text == "":
        return result

    result["requested"] = True
    src = Path(license_text).expanduser().resolve()
    pkg_dir = Path(trial_root_text).expanduser().resolve() / "radarsimpy"
    result["source_path"] = str(src)
    if not src.exists() or (not src.is_file()):
        result["error"] = f"license file missing: {src}"
        return result
    if not pkg_dir.exists() or (not pkg_dir.is_dir()):
        result["error"] = f"radarsimpy package directory missing: {pkg_dir}"
        return result

    staged_name = src.name
    lower_name = staged_name.lower()
    if (not lower_name.startswith("license_radarsimpy")) or (not lower_name.endswith(".lic")):
        staged_name = "license_RadarSimPy_import.lic"
    staged = pkg_dir / staged_name
    result["staged_path"] = str(staged)
    if staged.exists():
        try:
            if staged.resolve() == src:
                result["staged"] = True
                result["method"] = "preexisting"
                return result
        except Exception:
            pass
        result["error"] = f"staged license path already occupied: {staged}"
        return result
    try:
        staged.symlink_to(src)
        result["staged"] = True
        result["method"] = "symlink"
        result["cleanup_required"] = True
        return result
    except Exception:
        try:
            shutil.copy2(str(src), str(staged))
            result["staged"] = True
            result["method"] = "copy"
            result["cleanup_required"] = True
            return result
        except Exception as exc:
            result["error"] = f"unable to stage license file for import-time lookup: {exc}"
            return result


def _cleanup_staged_license(stage_info: Dict[str, Any]) -> None:
    if not bool(stage_info.get("cleanup_required", False)):
        return
    staged_text = str(stage_info.get("staged_path", "")).strip()
    if staged_text == "":
        return
    staged = Path(staged_text).expanduser()
    try:
        if staged.is_symlink() or staged.exists():
            staged.unlink()
    except Exception:
        pass


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    output_summary_json = Path(args.output_summary_json).expanduser().resolve()
    output_summary_json.parent.mkdir(parents=True, exist_ok=True)

    py_bin = _resolve_python_bin(args.python_bin)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"src{os.pathsep}{env['PYTHONPATH']}" if "PYTHONPATH" in env else "src"
    license_stage_info: Dict[str, Any] = {
        "requested": False,
        "staged": False,
        "method": "",
        "source_path": "",
        "staged_path": "",
        "cleanup_required": False,
        "error": "",
    }

    trial_pkg_root_text = "" if args.trial_package_root is None else str(args.trial_package_root).strip()
    libcompat_dir_text = "" if args.libcompat_dir is None else str(args.libcompat_dir).strip()
    license_file_text = "" if args.license_file is None else str(args.license_file).strip()
    if bool(args.with_real_runtime) and str(args.runtime_license_tier).strip().lower() == "trial":
        if trial_pkg_root_text == "":
            trial_pkg_root_text = DEFAULT_TRIAL_PACKAGE_ROOT
        if libcompat_dir_text == "":
            libcompat_dir_text = DEFAULT_LIBCOMPAT_DIR

    if bool(args.with_real_runtime):
        if trial_pkg_root_text != "":
            trial_pkg_root = Path(trial_pkg_root_text).expanduser()
            if not trial_pkg_root.is_absolute():
                trial_pkg_root = (repo_root / trial_pkg_root).resolve()
            env["PYTHONPATH"] = f"{env['PYTHONPATH']}{os.pathsep}{trial_pkg_root}"
            env[RADARSIMPY_PACKAGE_ROOT_ENV] = str(trial_pkg_root)
        if libcompat_dir_text != "":
            libcompat_dir = Path(libcompat_dir_text).expanduser()
            if not libcompat_dir.is_absolute():
                libcompat_dir = (repo_root / libcompat_dir).resolve()
            env["LD_LIBRARY_PATH"] = f"{libcompat_dir}{os.pathsep}{env.get('LD_LIBRARY_PATH', '')}"
            env[RADARSIMPY_LIBCOMPAT_DIR_ENV] = str(libcompat_dir)
        if license_file_text != "":
            license_file = Path(license_file_text).expanduser()
            if not license_file.is_absolute():
                license_file = (repo_root / license_file).resolve()
            else:
                license_file = license_file.resolve()
            env[RADARSIMPY_LICENSE_FILE_ENV] = str(license_file)
            license_file_text = str(license_file)
        license_stage_info = _stage_license_for_import_time_lookup(
            trial_package_root=str(trial_pkg_root_text),
            license_file=str(license_file_text),
        )
        if bool(license_stage_info.get("requested", False)) and not bool(
            license_stage_info.get("staged", False)
        ):
            stage_error = str(license_stage_info.get("error", "")).strip()
            raise RuntimeError(
                "failed to stage RadarSimPy license for import-time lookup: "
                f"{stage_error or 'unknown staging error'}"
            )

    sim_ref_cmd: List[str] = [py_bin, "scripts/validate_radarsimpy_simulator_reference_parity_optional.py"]
    sim_ref_json = output_summary_json.parent / "radarsimpy_simulator_reference_parity_from_smoke.json"
    sim_ref_cmd.extend(["--output-json", str(sim_ref_json)])
    if bool(args.with_real_runtime):
        sim_ref_cmd.append("--require-runtime")

    steps_spec: List[Dict[str, Any]] = [
        {
            "name": "validate_radarsimpy_api_coverage_excluding_sim_lidar",
            "cmd": [py_bin, "scripts/validate_radarsimpy_api_coverage_excluding_sim_lidar.py"],
        },
        {
            "name": "validate_radarsimpy_runtime_license_policy",
            "cmd": [py_bin, "scripts/validate_radarsimpy_runtime_license_policy.py"],
        },
        {
            "name": "validate_radarsimpy_processing_core_fallback",
            "cmd": [py_bin, "scripts/validate_radarsimpy_processing_core_fallback.py"],
        },
        {
            "name": "validate_radarsimpy_root_model_core_fallback",
            "cmd": [py_bin, "scripts/validate_radarsimpy_root_model_core_fallback.py"],
        },
        {
            "name": "validate_radarsimpy_simulator_core_fallback",
            "cmd": [py_bin, "scripts/validate_radarsimpy_simulator_core_fallback.py"],
        },
        {
            "name": "validate_radarsimpy_simulator_reference_parity_optional",
            "cmd": sim_ref_cmd,
        },
        {
            "name": "validate_run_radarsimpy_simulator_reference_parity_optional",
            "cmd": [py_bin, "scripts/validate_run_radarsimpy_simulator_reference_parity_optional.py"],
        },
        {
            "name": "validate_run_radarsimpy_layered_parity_suite",
            "cmd": [py_bin, "scripts/validate_run_radarsimpy_layered_parity_suite.py"],
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
        {
            "name": "validate_install_radarsimpy_ci_workflow",
            "cmd": [py_bin, "scripts/validate_install_radarsimpy_ci_workflow.py"],
        },
        {
            "name": "validate_show_radarsimpy_progress",
            "cmd": [py_bin, "scripts/validate_show_radarsimpy_progress.py"],
        },
        {
            "name": "validate_show_radarsimpy_function_progress",
            "cmd": [py_bin, "scripts/validate_show_radarsimpy_function_progress.py"],
        },
        {
            "name": "validate_build_radarsimpy_signature_manifest",
            "cmd": [py_bin, "scripts/validate_build_radarsimpy_signature_manifest.py"],
        },
        {
            "name": "validate_build_radarsimpy_native_parity_fixtures",
            "cmd": [py_bin, "scripts/validate_build_radarsimpy_native_parity_fixtures.py"],
        },
        {
            "name": "validate_run_radarsimpy_readiness_checkpoint_report",
            "cmd": [py_bin, "scripts/validate_run_radarsimpy_readiness_checkpoint_report.py"],
        },
    ]
    if not bool(args.skip_readiness_runner_validator):
        steps_spec.append(
            {
                "name": "validate_run_radarsimpy_readiness_checkpoint",
                "cmd": [py_bin, "scripts/validate_run_radarsimpy_readiness_checkpoint.py"],
            }
        )

    if bool(args.with_real_runtime):
        cmd = [
            py_bin,
            "scripts/run_radarsimpy_wrapper_integration_gate.py",
            "--with-real-runtime",
            "--output-summary-json",
            str(output_summary_json.parent / "radarsimpy_wrapper_integration_gate_real_from_smoke.json"),
            "--runtime-license-tier",
            str(args.runtime_license_tier),
        ]
        if trial_pkg_root_text != "":
            cmd.extend(["--trial-package-root", trial_pkg_root_text])
        if libcompat_dir_text != "":
            cmd.extend(["--libcompat-dir", libcompat_dir_text])
        if license_file_text != "":
            cmd.extend(["--license-file", license_file_text])
        steps_spec.append(
            {
                "name": "run_radarsimpy_wrapper_integration_gate_real_runtime",
                "cmd": cmd,
            }
        )

    steps: List[Dict[str, Any]] = []
    try:
        for row in steps_spec:
            steps.append(
                _run_step(
                    name=str(row["name"]),
                    cmd=list(row["cmd"]),
                    cwd=repo_root,
                    env=env,
                )
            )
    finally:
        _cleanup_staged_license(license_stage_info)

    pass_count = int(sum(1 for row in steps if bool(row.get("pass", False))))
    fail_count = int(len(steps) - pass_count)
    gate_pass = bool(fail_count == 0)

    summary = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "python_bin": str(py_bin),
        "with_real_runtime": bool(args.with_real_runtime),
        "runtime_license_tier": str(args.runtime_license_tier),
        "trial_package_root": str(trial_pkg_root_text),
        "libcompat_dir": str(libcompat_dir_text),
        "license_file": str(license_file_text),
        "import_time_license_artifact": license_stage_info,
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
