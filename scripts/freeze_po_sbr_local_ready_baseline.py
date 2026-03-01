#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y_%m_%d_%H%M%S")


def parse_args() -> argparse.Namespace:
    stamp = _utc_stamp()
    p = argparse.ArgumentParser(
        description=(
            "Freeze local PO-SBR ready-state evidence into a baseline directory "
            "with immutable copies and sha256 manifest."
        )
    )
    p.add_argument(
        "--local-ready-summary-json",
        required=True,
        help="Input summary JSON from scripts/run_po_sbr_local_ready_regression.py",
    )
    p.add_argument(
        "--output-dir",
        default=f"docs/reports/baselines/po_sbr_local_ready_{stamp}",
        help="Output baseline directory",
    )
    p.add_argument(
        "--manifest-json",
        default=None,
        help="Output baseline manifest JSON path (default: <output-dir>/baseline_manifest.json)",
    )
    p.add_argument(
        "--strict-ready",
        action="store_true",
        help="Exit non-zero unless source local-ready summary overall_status=ready",
    )
    return p.parse_args()


def _resolve_path(raw_path: str, cwd: Path) -> Path:
    path = Path(str(raw_path)).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (cwd / path).resolve()


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if len(chunk) == 0:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _copy_with_meta(src: Path, dst: Path) -> Dict[str, Any]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {
        "source_path": str(src),
        "frozen_path": str(dst),
        "size_bytes": int(dst.stat().st_size),
        "sha256": _sha256(dst),
    }


def _required_paths(local_payload: Mapping[str, Any], cwd: Path) -> Dict[str, Path]:
    reports = _mapping(local_payload.get("reports"))
    golden = _mapping(reports.get("golden_path"))
    kpi = _mapping(reports.get("kpi_campaign"))
    matrix = _mapping(reports.get("kpi_scenario_matrix"))
    gate = _mapping(reports.get("gate_lock"))

    required = {
        "scene_backend_golden_path": _resolve_path(str(golden.get("summary_json", "")), cwd=cwd),
        "scene_backend_kpi_campaign": _resolve_path(str(kpi.get("summary_json", "")), cwd=cwd),
        "scene_backend_kpi_scenario_matrix": _resolve_path(str(matrix.get("summary_json", "")), cwd=cwd),
        "po_sbr_physical_full_track_gate_lock": _resolve_path(str(gate.get("summary_json", "")), cwd=cwd),
        "po_sbr_physical_full_track_stability": _resolve_path(str(gate.get("stability_summary_json", "")), cwd=cwd),
        "po_sbr_realism_threshold_hardening": _resolve_path(str(gate.get("hardening_summary_json", "")), cwd=cwd),
        "po_sbr_physical_full_track_bundle": _resolve_path(
            str(local_payload.get("full_track_bundle_summary_json", "")),
            cwd=cwd,
        ),
        "po_sbr_local_ready_regression": _resolve_path(
            str(local_payload.get("_source_summary_json", "")),
            cwd=cwd,
        ),
    }
    for name, path in required.items():
        if not path.exists():
            raise FileNotFoundError(f"required baseline source missing [{name}]: {path}")
    return required


def main() -> None:
    args = parse_args()
    cwd = Path.cwd().resolve()

    local_ready_summary_json = _resolve_path(args.local_ready_summary_json, cwd=cwd)
    if not local_ready_summary_json.exists():
        raise FileNotFoundError(f"local-ready summary not found: {local_ready_summary_json}")

    local_payload = _load_json(local_ready_summary_json)
    local_payload["_source_summary_json"] = str(local_ready_summary_json)
    overall_status = str(_mapping(local_payload.get("summary")).get("overall_status", "")).strip()
    if overall_status == "":
        raise ValueError("local-ready summary missing summary.overall_status")

    output_dir = _resolve_path(args.output_dir, cwd=cwd)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_json = (
        _resolve_path(args.manifest_json, cwd=cwd)
        if args.manifest_json is not None
        else (output_dir / "baseline_manifest.json").resolve()
    )
    manifest_json.parent.mkdir(parents=True, exist_ok=True)

    sources = _required_paths(local_payload=local_payload, cwd=cwd)
    alias_name = {
        "scene_backend_golden_path": "scene_backend_golden_path.json",
        "scene_backend_kpi_campaign": "scene_backend_kpi_campaign.json",
        "scene_backend_kpi_scenario_matrix": "scene_backend_kpi_scenario_matrix.json",
        "po_sbr_physical_full_track_gate_lock": "po_sbr_physical_full_track_gate_lock.json",
        "po_sbr_physical_full_track_stability": "po_sbr_physical_full_track_stability.json",
        "po_sbr_realism_threshold_hardening": "po_sbr_realism_threshold_hardening.json",
        "po_sbr_physical_full_track_bundle": "po_sbr_physical_full_track_bundle.json",
        "po_sbr_local_ready_regression": "po_sbr_local_ready_regression.json",
    }

    frozen_files: Dict[str, Dict[str, Any]] = {}
    for key, src in sources.items():
        frozen_files[key] = _copy_with_meta(src=src, dst=(output_dir / alias_name[key]).resolve())

    baseline_status = "ready" if overall_status == "ready" else "blocked"
    report = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(cwd),
        "baseline_status": baseline_status,
        "source_local_ready_summary_json": str(local_ready_summary_json),
        "source_overall_status": overall_status,
        "output_dir": str(output_dir),
        "manifest_json": str(manifest_json),
        "frozen_files": frozen_files,
    }
    manifest_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("PO-SBR local ready baseline freeze completed.")
    print(f"  baseline_status: {baseline_status}")
    print(f"  source_overall_status: {overall_status}")
    print(f"  frozen_file_count: {len(frozen_files)}")
    print(f"  output_dir: {output_dir}")
    print(f"  manifest_json: {manifest_json}")

    if bool(args.strict_ready) and baseline_status != "ready":
        raise RuntimeError(f"baseline source is not ready: {overall_status}")


if __name__ == "__main__":
    main()
