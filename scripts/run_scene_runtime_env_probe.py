#!/usr/bin/env python3
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from avxsim.runtime_coupling import detect_runtime_modules


DEFAULT_RUNTIME_SPECS: Dict[str, Dict[str, Any]] = {
    "sionna_rt_mitsuba_runtime": {
        "required_modules": ("mitsuba", "drjit"),
        "repo_candidates": ("external/sionna",),
        "supported_systems": ("Darwin", "Linux", "Windows"),
        "requires_nvidia": False,
    },
    "sionna_runtime": {
        "required_modules": ("sionna", "tensorflow"),
        "repo_candidates": ("external/sionna",),
        "supported_systems": ("Darwin", "Linux", "Windows"),
        "requires_nvidia": False,
    },
    "sionna_rt_full_runtime": {
        "required_modules": ("sionna.rt", "mitsuba", "drjit"),
        "repo_candidates": ("external/sionna",),
        "supported_systems": ("Darwin", "Linux", "Windows"),
        "requires_nvidia": False,
    },
    "po_sbr_runtime": {
        "required_modules": ("rtxpy", "igl"),
        "repo_candidates": (
            "external/PO-SBR-Python",
            "external/po-sbr-python",
            "external/po_sbr_python",
        ),
        "supported_systems": ("Linux",),
        "requires_nvidia": True,
    },
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Probe runtime readiness for direct scene backend coupling")
    p.add_argument(
        "--workspace-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Workspace root containing external/ repositories",
    )
    p.add_argument(
        "--drjit-libllvm-path",
        default="",
        help="Optional DRJIT_LIBLLVM_PATH override for probing sionna.rt availability",
    )
    p.add_argument("--output-summary-json", required=True, help="Output summary JSON path")
    return p.parse_args()


def _resolve_existing_paths(workspace_root: Path, rel_paths: Sequence[str]) -> Tuple[List[str], List[str]]:
    found: List[str] = []
    missing: List[str] = []
    for rel in rel_paths:
        path = workspace_root / str(rel)
        if path.exists():
            found.append(str(path))
        else:
            missing.append(str(path))
    return found, missing


def _missing_required_modules(
    report: Mapping[str, Mapping[str, Any]],
    required_modules: Sequence[str],
) -> List[str]:
    missing: List[str] = []
    for name in required_modules:
        if not bool(report.get(name, {}).get("available", False)):
            missing.append(str(name))
    return missing


def _detect_nvidia_runtime() -> Dict[str, Any]:
    exe = shutil.which("nvidia-smi")
    if exe is None:
        return {
            "available": False,
            "executable": None,
            "driver_info": None,
        }
    try:
        proc = subprocess.run(
            [exe, "--query-gpu=name,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        return {
            "available": True,
            "executable": exe,
            "driver_info": lines,
        }
    except Exception as exc:  # pragma: no cover - env-dependent
        return {
            "available": False,
            "executable": exe,
            "driver_info": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def build_runtime_probe_summary(
    workspace_root: str,
    drjit_libllvm_path: Optional[str] = None,
) -> Dict[str, Any]:
    root = Path(workspace_root).resolve()
    system = platform.system()
    applied_overrides: Dict[str, Any] = {}
    if drjit_libllvm_path is not None and str(drjit_libllvm_path).strip() != "":
        libllvm_text = str(Path(str(drjit_libllvm_path).strip()).expanduser().resolve())
        os.environ["DRJIT_LIBLLVM_PATH"] = libllvm_text
        applied_overrides["DRJIT_LIBLLVM_PATH"] = {
            "path": libllvm_text,
            "exists": bool(Path(libllvm_text).exists()),
        }
    all_modules: List[str] = []
    for spec in DEFAULT_RUNTIME_SPECS.values():
        for module_name in spec["required_modules"]:
            text = str(module_name).strip()
            if text != "" and text not in all_modules:
                all_modules.append(text)

    module_report = detect_runtime_modules(all_modules)
    nvidia_report = _detect_nvidia_runtime()
    runtime_report: Dict[str, Any] = {}
    for runtime_name, spec in DEFAULT_RUNTIME_SPECS.items():
        required_modules = tuple(str(x) for x in spec["required_modules"])
        repo_candidates = tuple(str(x) for x in spec["repo_candidates"])
        supported_systems = tuple(str(x) for x in spec.get("supported_systems", ()))
        requires_nvidia = bool(spec.get("requires_nvidia", False))
        found_paths, missing_paths = _resolve_existing_paths(root, repo_candidates)
        missing_modules = _missing_required_modules(module_report, required_modules=required_modules)
        repo_found = len(found_paths) > 0
        platform_supported = (len(supported_systems) == 0) or (system in supported_systems)
        nvidia_available = bool(nvidia_report.get("available", False))
        blockers: List[str] = []
        if not repo_found:
            blockers.append("missing_repo")
        if len(missing_modules) > 0:
            blockers.append("missing_required_modules")
        if not platform_supported:
            blockers.append(f"unsupported_platform:{system}")
        if requires_nvidia and (not nvidia_available):
            blockers.append("missing_nvidia_runtime")
        ready = len(blockers) == 0
        runtime_report[runtime_name] = {
            "ready": bool(ready),
            "required_modules": list(required_modules),
            "missing_required_modules": missing_modules,
            "repo_candidates": list(repo_candidates),
            "found_repo_paths": found_paths,
            "missing_repo_paths": missing_paths,
            "repo_found": bool(repo_found),
            "supported_systems": list(supported_systems),
            "platform_supported": bool(platform_supported),
            "requires_nvidia": bool(requires_nvidia),
            "nvidia_available": bool(nvidia_available),
            "blockers": blockers,
            "status": "ready" if ready else "blocked",
        }

    return {
        "workspace_root": str(root),
        "applied_overrides": applied_overrides,
        "python": {
            "version": str(sys.version).strip(),
            "version_info": {
                "major": int(sys.version_info.major),
                "minor": int(sys.version_info.minor),
                "micro": int(sys.version_info.micro),
            },
            "platform": platform.platform(),
            "system": system,
        },
        "module_report": module_report,
        "nvidia_runtime": nvidia_report,
        "runtime_report": runtime_report,
    }


def main() -> None:
    args = parse_args()
    summary = build_runtime_probe_summary(
        workspace_root=str(args.workspace_root),
        drjit_libllvm_path=str(args.drjit_libllvm_path),
    )

    out = Path(args.output_summary_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Scene runtime environment probe completed.")
    for runtime_name, runtime_info in summary["runtime_report"].items():
        print(f"  {runtime_name}_ready: {runtime_info['ready']}")
        print(f"  {runtime_name}_missing_required_modules: {runtime_info['missing_required_modules']}")
        print(f"  {runtime_name}_blockers: {runtime_info['blockers']}")
        print(f"  {runtime_name}_repo_found: {runtime_info['repo_found']}")
    print(f"  output_summary_json: {out}")


if __name__ == "__main__":
    main()
