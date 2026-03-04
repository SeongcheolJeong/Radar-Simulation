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


DEFAULT_TRIAL_PACKAGE_ROOT = "external/radarsimpy_trial/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU"
DEFAULT_LIBCOMPAT_DIR = "external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu"
RADARSIMPY_LICENSE_FILE_ENV = "RADARSIMPY_LICENSE_FILE"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run layered white-box vs RadarSimPy black-box parity suite and emit one summary JSON."
        )
    )
    p.add_argument("--output-json", required=True)
    p.add_argument("--python-bin", default="")
    p.add_argument("--trial-output-json", default="")
    p.add_argument("--production-output-json", default="")
    p.add_argument("--with-production-track", action="store_true")
    p.add_argument("--require-runtime-trial", action="store_true")
    p.add_argument("--require-runtime-production", action="store_true")
    p.add_argument("--trial-package-root", default="")
    p.add_argument("--libcompat-dir", default="")
    p.add_argument("--license-file", default="")
    p.add_argument("--allow-failures", action="store_true")
    return p.parse_args()


def _resolve_python_bin(raw: str, repo_root: Path) -> str:
    text = str(raw).strip()
    if text != "":
        p = Path(text).expanduser()
        if p.exists():
            if p.is_absolute():
                return str(p.resolve())
            return str((repo_root / p).resolve())
        return text

    for candidate in (
        repo_root / ".venv" / "bin" / "python",
        repo_root / ".venv-po-sbr" / "bin" / "python",
    ):
        if candidate.exists():
            return str(candidate)
    return str(sys.executable)


def _resolve_output_path(raw: str, *, repo_root: Path, default_path: Path) -> Path:
    text = str(raw).strip()
    if text == "":
        p = default_path
    else:
        p = Path(text).expanduser()
        if not p.is_absolute():
            p = (repo_root / p).resolve()
        else:
            p = p.resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _run(cmd: List[str], *, cwd: Path, env: Mapping[str, str]) -> Dict[str, Any]:
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
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-120:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-120:]),
    }


def _load_json_if_exists(path: Path) -> Dict[str, Any] | None:
    if not path.exists() or (not path.is_file()):
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    return payload


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

    staged = pkg_dir / "license_RadarSimPy_env.lic"
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

    out_json = _resolve_output_path(
        str(args.output_json),
        repo_root=repo_root,
        default_path=repo_root / "docs/reports/radarsimpy_layered_parity_suite_latest.json",
    )
    trial_out = _resolve_output_path(
        str(args.trial_output_json),
        repo_root=repo_root,
        default_path=out_json.parent / "radarsimpy_layered_parity_trial.json",
    )
    production_out = _resolve_output_path(
        str(args.production_output_json),
        repo_root=repo_root,
        default_path=out_json.parent / "radarsimpy_layered_parity_production.json",
    )

    py_bin = _resolve_python_bin(str(args.python_bin), repo_root=repo_root)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"src{os.pathsep}{env['PYTHONPATH']}" if "PYTHONPATH" in env else "src"

    trial_pkg_root_text = str(args.trial_package_root).strip()
    libcompat_dir_text = str(args.libcompat_dir).strip()
    license_file_text = str(args.license_file).strip()

    runtime_requested = bool(args.require_runtime_trial or args.require_runtime_production or args.with_production_track)
    if runtime_requested:
        if trial_pkg_root_text == "":
            trial_pkg_root_text = DEFAULT_TRIAL_PACKAGE_ROOT
        if libcompat_dir_text == "":
            libcompat_dir_text = DEFAULT_LIBCOMPAT_DIR

    if trial_pkg_root_text != "":
        trial_pkg_root = Path(trial_pkg_root_text).expanduser()
        if not trial_pkg_root.is_absolute():
            trial_pkg_root = (repo_root / trial_pkg_root).resolve()
        env["PYTHONPATH"] = f"{env['PYTHONPATH']}{os.pathsep}{trial_pkg_root}"
        trial_pkg_root_text = str(trial_pkg_root)

    if libcompat_dir_text != "":
        libcompat_dir = Path(libcompat_dir_text).expanduser()
        if not libcompat_dir.is_absolute():
            libcompat_dir = (repo_root / libcompat_dir).resolve()
        env["LD_LIBRARY_PATH"] = f"{libcompat_dir}{os.pathsep}{env.get('LD_LIBRARY_PATH', '')}"
        libcompat_dir_text = str(libcompat_dir)

    if license_file_text != "":
        license_file = Path(license_file_text).expanduser()
        if not license_file.is_absolute():
            license_file = (repo_root / license_file).resolve()
        else:
            license_file = license_file.resolve()
        license_file_text = str(license_file)
        env[RADARSIMPY_LICENSE_FILE_ENV] = license_file_text

    stage_info = _stage_license_for_import_time_lookup(
        trial_package_root=trial_pkg_root_text,
        license_file=license_file_text,
    )
    if bool(stage_info.get("requested", False)) and (not bool(stage_info.get("staged", False))):
        stage_error = str(stage_info.get("error", "")).strip()
        raise RuntimeError(
            "failed to stage RadarSimPy license for import-time lookup: "
            f"{stage_error or 'unknown staging error'}"
        )

    tracks: List[Dict[str, Any]] = []
    try:
        trial_cmd = [
            py_bin,
            "scripts/validate_radarsimpy_layered_reference_parity_optional.py",
            "--track",
            "trial",
            "--output-json",
            str(trial_out),
        ]
        if bool(args.require_runtime_trial):
            trial_cmd.append("--require-runtime")

        trial_run = _run(trial_cmd, cwd=repo_root, env=env)
        trial_payload = _load_json_if_exists(trial_out)
        tracks.append(
            {
                "name": "trial",
                "required": bool(args.require_runtime_trial),
                "run": trial_run,
                "report_json": str(trial_out),
                "report": trial_payload,
            }
        )

        if bool(args.with_production_track):
            prod_cmd = [
                py_bin,
                "scripts/validate_radarsimpy_layered_reference_parity_optional.py",
                "--track",
                "production",
                "--output-json",
                str(production_out),
            ]
            if bool(args.require_runtime_production):
                prod_cmd.append("--require-runtime")
            prod_run = _run(prod_cmd, cwd=repo_root, env=env)
            prod_payload = _load_json_if_exists(production_out)
            tracks.append(
                {
                    "name": "production",
                    "required": bool(args.require_runtime_production),
                    "run": prod_run,
                    "report_json": str(production_out),
                    "report": prod_payload,
                }
            )
    finally:
        _cleanup_staged_license(stage_info)

    pass_count = int(sum(1 for row in tracks if bool((row.get("run") or {}).get("pass", False))))
    fail_count = int(len(tracks) - pass_count)

    required_fail_count = int(
        sum(
            1
            for row in tracks
            if bool(row.get("required", False)) and (not bool((row.get("run") or {}).get("pass", False)))
        )
    )

    gate_pass = bool(required_fail_count == 0 and fail_count == 0)

    summary = {
        "version": 1,
        "report_name": "radarsimpy_layered_parity_suite",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(repo_root),
        "python_bin": str(py_bin),
        "with_production_track": bool(args.with_production_track),
        "require_runtime_trial": bool(args.require_runtime_trial),
        "require_runtime_production": bool(args.require_runtime_production),
        "trial_package_root": trial_pkg_root_text,
        "libcompat_dir": libcompat_dir_text,
        "license_file": license_file_text,
        "import_time_license_artifact": stage_info,
        "track_count": int(len(tracks)),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "required_fail_count": required_fail_count,
        "pass": gate_pass,
        "tracks": tracks,
    }

    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("RadarSimPy layered parity suite completed.")
    print(f"  pass: {gate_pass}")
    print(f"  pass_count: {pass_count}")
    print(f"  fail_count: {fail_count}")
    print(f"  required_fail_count: {required_fail_count}")
    print(f"  output_json: {out_json}")

    if (not gate_pass) and (not bool(args.allow_failures)):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
