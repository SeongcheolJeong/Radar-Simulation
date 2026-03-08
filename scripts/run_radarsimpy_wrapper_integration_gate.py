#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping

FREE_TIER_WARNING_MARKERS = (
    "no license file path provided",
    "running in free tier mode",
)
DEFAULT_TRIAL_PACKAGE_ROOT = "external/radarsimpy_trial/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU"
DEFAULT_LIBCOMPAT_DIR = "external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu"
RADARSIMPY_LICENSE_FILE_ENV = "RADARSIMPY_LICENSE_FILE"
RADARSIMPY_PACKAGE_ROOT_ENV = "RADARSIMPY_PACKAGE_ROOT"
RADARSIMPY_LIBCOMPAT_DIR_ENV = "RADARSIMPY_LIBCOMPAT_DIR"


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
        default="",
        help=(
            "RadarSimPy package root used when --with-real-runtime is set. "
            "In trial tier, empty value auto-resolves to bundled trial package path."
        ),
    )
    p.add_argument(
        "--libcompat-dir",
        default="",
        help=(
            "Shared library directory for RadarSimPy runtime. "
            "In trial tier, empty value auto-resolves to bundled libcompat path."
        ),
    )
    p.add_argument(
        "--runtime-license-tier",
        choices=("trial", "production"),
        default="trial",
        help=(
            "Runtime license tier policy for --with-real-runtime checks. "
            "'production' fails on free-tier warning markers and runs strict pilot "
            "without --trial-free-tier-geometry."
        ),
    )
    p.add_argument(
        "--license-file",
        default="",
        help=(
            "Optional RadarSimPy license file path. "
            f"When provided, sets {RADARSIMPY_LICENSE_FILE_ENV} for real-runtime checks."
        ),
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


def _contains_free_tier_warning(stderr_text: str) -> bool:
    lower = str(stderr_text).lower()
    return any(marker in lower for marker in FREE_TIER_WARNING_MARKERS)


def _extract_first_bool_line(stdout_text: str) -> bool | None:
    for raw in str(stdout_text).splitlines():
        token = raw.strip().lower()
        if token == "true":
            return True
        if token == "false":
            return False
    return None


def _apply_production_policy_to_check(result: Dict[str, Any]) -> Dict[str, Any]:
    if _contains_free_tier_warning(str(result.get("stderr", ""))):
        result["ok"] = False
        result["policy_violation"] = "free_tier_warning_marker_detected"
    return result


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


def _run_real_runtime_license_status(
    repo_root: Path,
    env: Mapping[str, str],
) -> Dict[str, Any]:
    code = (
        f"import os\n"
        "import radarsimpy as rs\n"
        f"license_file = str(os.environ.get('{RADARSIMPY_LICENSE_FILE_ENV}', '')).strip()\n"
        "if license_file != '' and hasattr(rs, 'set_license'):\n"
        "    rs.set_license(license_file)\n"
        "is_licensed = bool(rs.is_licensed()) if hasattr(rs, 'is_licensed') else False\n"
        "license_info = rs.get_license_info() if hasattr(rs, 'get_license_info') else ''\n"
        "print(is_licensed)\n"
        "print(license_info)\n"
    )
    return _run([sys.executable, "-c", code], repo_root=repo_root, env=env)


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


def _cleanup_staged_license(stage_info: Mapping[str, Any]) -> None:
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
            "runtime_license_policy",
            [sys.executable, "scripts/validate_radarsimpy_runtime_license_policy.py"],
        ),
        (
            "api_coverage_excluding_sim_lidar",
            [sys.executable, "scripts/validate_radarsimpy_api_coverage_excluding_sim_lidar.py"],
        ),
        (
            "root_model_core_fallback",
            [sys.executable, "scripts/validate_radarsimpy_root_model_core_fallback.py"],
        ),
        (
            "simulator_core_fallback",
            [sys.executable, "scripts/validate_radarsimpy_simulator_core_fallback.py"],
        ),
        (
            "simulator_reference_parity_optional",
            [sys.executable, "scripts/validate_radarsimpy_simulator_reference_parity_optional.py"],
        ),
        (
            "layered_parity_runner_validator",
            [sys.executable, "scripts/validate_run_radarsimpy_layered_parity_suite.py"],
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
        staged_license_info: Dict[str, Any] = {
            "requested": False,
            "staged": False,
            "method": "",
            "source_path": "",
            "staged_path": "",
            "cleanup_required": False,
            "error": "",
        }
        runtime_license_tier = str(args.runtime_license_tier).strip().lower()
        env_real = dict(env_base)
        trial_pkg_root_text = str(args.trial_package_root).strip()
        libcompat_dir_text = str(args.libcompat_dir).strip()
        license_file_text = str(args.license_file).strip()
        if runtime_license_tier == "trial":
            if trial_pkg_root_text == "":
                trial_pkg_root_text = DEFAULT_TRIAL_PACKAGE_ROOT
            if libcompat_dir_text == "":
                libcompat_dir_text = DEFAULT_LIBCOMPAT_DIR

        inject_trial_pkg = trial_pkg_root_text != ""
        inject_libcompat = libcompat_dir_text != ""

        trial_pkg_root_resolved = ""
        if inject_trial_pkg:
            trial_pkg_root = Path(trial_pkg_root_text).expanduser()
            if not trial_pkg_root.is_absolute():
                trial_pkg_root = (repo_root / trial_pkg_root).resolve()
            trial_pkg_root_resolved = str(trial_pkg_root)
            env_real["PYTHONPATH"] = f"{env_base['PYTHONPATH']}:{trial_pkg_root_resolved}"
            env_real[RADARSIMPY_PACKAGE_ROOT_ENV] = trial_pkg_root_resolved

        libcompat_dir_resolved = ""
        if inject_libcompat:
            libcompat_dir = Path(libcompat_dir_text).expanduser()
            if not libcompat_dir.is_absolute():
                libcompat_dir = (repo_root / libcompat_dir).resolve()
            libcompat_dir_resolved = str(libcompat_dir)
            env_real["LD_LIBRARY_PATH"] = f"{libcompat_dir_resolved}:{env_real.get('LD_LIBRARY_PATH', '')}"
            env_real[RADARSIMPY_LIBCOMPAT_DIR_ENV] = libcompat_dir_resolved

        license_file_resolved = ""
        if license_file_text != "":
            license_file = Path(license_file_text).expanduser()
            if not license_file.is_absolute():
                license_file = (repo_root / license_file).resolve()
            else:
                license_file = license_file.resolve()
            license_file_resolved = str(license_file)
            env_real[RADARSIMPY_LICENSE_FILE_ENV] = license_file_resolved

        staged_license_info = _stage_license_for_import_time_lookup(
            trial_package_root=trial_pkg_root_resolved,
            license_file=license_file_resolved,
        )
        real_runtime["import_time_license_artifact"] = dict(staged_license_info)
        if bool(staged_license_info.get("requested", False)) and not bool(
            staged_license_info.get("staged", False)
        ):
            staged_error = str(staged_license_info.get("error", "")).strip()
            raise RuntimeError(
                "failed to stage RadarSimPy license for import-time lookup: "
                f"{staged_error or 'unknown staging error'}"
            )

        try:
            probe = _run_real_runtime_probe(repo_root=repo_root, env=env_real)
            if runtime_license_tier == "production":
                probe = _apply_production_policy_to_check(probe)
            probe["check_name"] = "real_runtime_api_probe"
            checks.append(probe)
            real_runtime["api_probe"] = probe
            real_runtime["runtime_license_tier"] = runtime_license_tier
            real_runtime["trial_package_root"] = trial_pkg_root_resolved
            real_runtime["libcompat_dir"] = libcompat_dir_resolved
            real_runtime["license_file"] = license_file_resolved
            real_runtime["trial_runtime_path_injection"] = {
                "trial_package_root": bool(inject_trial_pkg),
                "libcompat_dir": bool(inject_libcompat),
            }

            license_status = _run_real_runtime_license_status(repo_root=repo_root, env=env_real)
            if runtime_license_tier == "production":
                license_activated = _extract_first_bool_line(str(license_status.get("stdout", "")))
                license_status["license_activated"] = license_activated
                if license_activated is not True:
                    license_status["ok"] = False
                    license_status["policy_violation"] = "license_not_activated"
            license_status["check_name"] = "real_runtime_license_status"
            checks.append(license_status)
            real_runtime["license_status"] = license_status

            # Enforce simulator parity validator in the same real-runtime environment.
            sim_parity_json = summary_path.parent / "radarsimpy_simulator_reference_parity_real_runtime.json"
            sim_parity = _run(
                [
                    sys.executable,
                    "scripts/validate_radarsimpy_simulator_reference_parity_optional.py",
                    "--require-runtime",
                    "--output-json",
                    str(sim_parity_json),
                ],
                repo_root=repo_root,
                env=env_real,
            )
            if runtime_license_tier == "production":
                sim_parity = _apply_production_policy_to_check(sim_parity)
            sim_parity["check_name"] = "simulator_reference_parity_real_runtime"
            checks.append(sim_parity)
            real_runtime["simulator_reference_parity"] = sim_parity
            real_runtime["simulator_reference_parity_json"] = str(sim_parity_json)

            layered_suite_json = summary_path.parent / "radarsimpy_layered_parity_suite_real_runtime.json"
            layered_suite_cmd = [
                sys.executable,
                "scripts/run_radarsimpy_layered_parity_suite.py",
                "--output-json",
                str(layered_suite_json),
                "--require-runtime-trial",
            ]
            if trial_pkg_root_text != "":
                layered_suite_cmd.extend(["--trial-package-root", trial_pkg_root_text])
            if libcompat_dir_text != "":
                layered_suite_cmd.extend(["--libcompat-dir", libcompat_dir_text])
            if license_file_resolved != "":
                layered_suite_cmd.extend(["--license-file", license_file_resolved])
            if runtime_license_tier == "production":
                layered_suite_cmd.extend(["--with-production-track", "--require-runtime-production"])
            layered_suite = _run(layered_suite_cmd, repo_root=repo_root, env=env_real)
            if runtime_license_tier == "production":
                layered_suite = _apply_production_policy_to_check(layered_suite)
            layered_suite["check_name"] = "layered_parity_suite_real_runtime"
            checks.append(layered_suite)
            real_runtime["layered_parity_suite"] = layered_suite
            real_runtime["layered_parity_suite_json"] = str(layered_suite_json)

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
                "--runtime-device",
                "cpu",
            ]
            if runtime_license_tier == "trial":
                pilot_cmd.append("--trial-free-tier-geometry")
            pilot_result = _run(pilot_cmd, repo_root=repo_root, env=env_real)
            if runtime_license_tier == "production":
                pilot_result = _apply_production_policy_to_check(pilot_result)
            pilot_result["check_name"] = "real_runtime_strict_pilot"
            checks.append(pilot_result)
            real_runtime["strict_pilot"] = pilot_result
            real_runtime["pilot_output_root"] = str(pilot_output_root)
            real_runtime["pilot_summary_json"] = str(pilot_summary)
        finally:
            _cleanup_staged_license(staged_license_info)

    pass_count = int(sum(1 for item in checks if bool(item.get("ok"))))
    fail_count = int(len(checks) - pass_count)
    summary: Dict[str, Any] = {
        "version": 1,
        "gate": "radarsimpy_wrapper_integration",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "with_real_runtime": bool(args.with_real_runtime),
        "runtime_license_tier": str(args.runtime_license_tier),
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
