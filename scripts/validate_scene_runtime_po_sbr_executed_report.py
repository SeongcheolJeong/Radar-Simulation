#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate executed PO-SBR runtime pilot summary report")
    p.add_argument("--summary-json", required=True, help="Path to PO-SBR pilot summary JSON")
    return p.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("summary json must be object")
    return payload


def _assert_path_exists(value: Any, key_name: str) -> None:
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"{key_name} must be non-empty string path")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{key_name} must be absolute path: {value}")
    if not path.exists():
        raise ValueError(f"{key_name} path not found: {value}")


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary_json).expanduser().resolve()
    if not summary_path.exists():
        raise FileNotFoundError(f"summary report not found: {summary_path}")

    summary = _load_json(summary_path)
    status = str(summary.get("pilot_status", "")).strip().lower()
    if status != "executed":
        raise ValueError(f"pilot_status must be 'executed', got: {summary.get('pilot_status')}")

    blockers = summary.get("blockers")
    if not isinstance(blockers, list):
        raise ValueError("blockers must be list")
    if len(blockers) != 0:
        raise ValueError(f"executed summary must have empty blockers, got: {blockers}")

    frame_count = int(summary.get("frame_count", 0))
    path_count = int(summary.get("path_count", 0))
    if frame_count <= 0:
        raise ValueError("frame_count must be > 0 for executed summary")
    if path_count <= 0:
        raise ValueError("path_count must be > 0 for executed summary")

    for key in ("scene_json", "output_dir", "path_list_json", "adc_cube_npz", "radar_map_npz"):
        _assert_path_exists(summary.get(key), key)

    runtime_resolution = summary.get("runtime_resolution")
    if not isinstance(runtime_resolution, dict):
        raise ValueError("runtime_resolution must be object for executed summary")
    if str(runtime_resolution.get("mode", "")).strip() != "runtime_provider":
        raise ValueError("runtime_resolution.mode must be runtime_provider")
    provider = str(runtime_resolution.get("runtime_provider", "")).strip()
    if not provider.endswith("generate_po_sbr_like_paths_from_posbr"):
        raise ValueError(f"unexpected runtime_provider: {provider}")

    diagnostics = summary.get("diagnostics")
    if not isinstance(diagnostics, dict):
        raise ValueError("diagnostics must be object")
    if str(diagnostics.get("platform", "")).strip() != "Linux":
        raise ValueError(f"executed report must come from Linux platform, got: {diagnostics.get('platform')}")

    command_hint = str(summary.get("recommended_linux_command", "")).strip()
    if command_hint == "":
        raise ValueError("recommended_linux_command must be non-empty")

    print("validate_scene_runtime_po_sbr_executed_report: pass")
    print(f"  summary_json: {summary_path}")
    print(f"  frame_count: {frame_count}")
    print(f"  path_count: {path_count}")


if __name__ == "__main__":
    main()
