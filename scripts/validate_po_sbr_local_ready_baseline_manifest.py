#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate PO-SBR local-ready baseline freeze manifest")
    p.add_argument("--manifest-json", required=True, help="Baseline manifest JSON path")
    p.add_argument(
        "--require-ready",
        action="store_true",
        help="Fail validation unless baseline_status=ready",
    )
    return p.parse_args()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("manifest json must be object")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if len(chunk) == 0:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _assert_file_entry(name: str, value: Any) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"frozen_files.{name} must be object")
    frozen_path = Path(str(value.get("frozen_path", ""))).expanduser()
    source_path = Path(str(value.get("source_path", ""))).expanduser()
    if not frozen_path.is_absolute():
        raise ValueError(f"frozen_files.{name}.frozen_path must be absolute")
    if not source_path.is_absolute():
        raise ValueError(f"frozen_files.{name}.source_path must be absolute")
    if not frozen_path.exists():
        raise ValueError(f"frozen_files.{name}.frozen_path missing: {frozen_path}")
    if not source_path.exists():
        raise ValueError(f"frozen_files.{name}.source_path missing: {source_path}")

    expected_size = int(value.get("size_bytes", -1))
    real_size = int(frozen_path.stat().st_size)
    if expected_size != real_size:
        raise ValueError(f"frozen_files.{name}.size_bytes mismatch: got={expected_size}, expected={real_size}")

    expected_sha = str(value.get("sha256", "")).strip().lower()
    if expected_sha == "":
        raise ValueError(f"frozen_files.{name}.sha256 missing")
    real_sha = _sha256(frozen_path)
    if expected_sha != real_sha:
        raise ValueError(f"frozen_files.{name}.sha256 mismatch")


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest_json).expanduser().resolve()
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")

    payload = _load_json(manifest_path)
    if int(payload.get("version", 0)) != 1:
        raise ValueError("version must be 1")

    baseline_status = str(payload.get("baseline_status", "")).strip()
    if baseline_status not in ("ready", "blocked"):
        raise ValueError(f"baseline_status invalid: {baseline_status}")

    frozen_files = payload.get("frozen_files")
    if not isinstance(frozen_files, Mapping):
        raise ValueError("frozen_files must be object")
    if len(frozen_files) == 0:
        raise ValueError("frozen_files must be non-empty")

    required_aliases = (
        "scene_backend_golden_path",
        "scene_backend_kpi_campaign",
        "scene_backend_kpi_scenario_matrix",
        "po_sbr_physical_full_track_gate_lock",
        "po_sbr_physical_full_track_stability",
        "po_sbr_realism_threshold_hardening",
        "po_sbr_physical_full_track_bundle",
        "po_sbr_local_ready_regression",
    )
    for alias in required_aliases:
        if alias not in frozen_files:
            raise ValueError(f"frozen_files missing alias: {alias}")
        _assert_file_entry(alias, frozen_files[alias])

    if args.require_ready and baseline_status != "ready":
        raise ValueError(f"baseline_status must be ready, got: {baseline_status}")

    print("validate_po_sbr_local_ready_baseline_manifest: pass")
    print(f"  manifest_json: {manifest_path}")
    print(f"  baseline_status: {baseline_status}")
    print(f"  frozen_file_count: {len(frozen_files)}")


if __name__ == "__main__":
    main()
