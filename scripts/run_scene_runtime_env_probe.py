#!/usr/bin/env python3
import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from avxsim.runtime_coupling import detect_runtime_modules


DEFAULT_RUNTIME_SPECS: Dict[str, Dict[str, Any]] = {
    "sionna_runtime": {
        "required_modules": ("sionna", "tensorflow"),
        "repo_candidates": ("external/sionna",),
    },
    "po_sbr_runtime": {
        "required_modules": ("po_sbr", "pyoptix", "optix"),
        "repo_candidates": (
            "external/PO-SBR-Python",
            "external/po-sbr-python",
            "external/po_sbr_python",
        ),
    },
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Probe runtime readiness for direct scene backend coupling")
    p.add_argument(
        "--workspace-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Workspace root containing external/ repositories",
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


def build_runtime_probe_summary(workspace_root: str) -> Dict[str, Any]:
    root = Path(workspace_root).resolve()
    all_modules: List[str] = []
    for spec in DEFAULT_RUNTIME_SPECS.values():
        for module_name in spec["required_modules"]:
            text = str(module_name).strip()
            if text != "" and text not in all_modules:
                all_modules.append(text)

    module_report = detect_runtime_modules(all_modules)
    runtime_report: Dict[str, Any] = {}
    for runtime_name, spec in DEFAULT_RUNTIME_SPECS.items():
        required_modules = tuple(str(x) for x in spec["required_modules"])
        repo_candidates = tuple(str(x) for x in spec["repo_candidates"])
        found_paths, missing_paths = _resolve_existing_paths(root, repo_candidates)
        missing_modules = _missing_required_modules(module_report, required_modules=required_modules)
        repo_found = len(found_paths) > 0
        ready = repo_found and (len(missing_modules) == 0)
        runtime_report[runtime_name] = {
            "ready": bool(ready),
            "required_modules": list(required_modules),
            "missing_required_modules": missing_modules,
            "repo_candidates": list(repo_candidates),
            "found_repo_paths": found_paths,
            "missing_repo_paths": missing_paths,
            "repo_found": bool(repo_found),
        }

    return {
        "workspace_root": str(root),
        "python": {
            "version": str(sys.version).strip(),
            "version_info": {
                "major": int(sys.version_info.major),
                "minor": int(sys.version_info.minor),
                "micro": int(sys.version_info.micro),
            },
            "platform": platform.platform(),
        },
        "module_report": module_report,
        "runtime_report": runtime_report,
    }


def main() -> None:
    args = parse_args()
    summary = build_runtime_probe_summary(workspace_root=str(args.workspace_root))

    out = Path(args.output_summary_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Scene runtime environment probe completed.")
    for runtime_name, runtime_info in summary["runtime_report"].items():
        print(f"  {runtime_name}_ready: {runtime_info['ready']}")
        print(f"  {runtime_name}_missing_required_modules: {runtime_info['missing_required_modules']}")
        print(f"  {runtime_name}_repo_found: {runtime_info['repo_found']}")
    print(f"  output_summary_json: {out}")


if __name__ == "__main__":
    main()
