#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


DEFAULT_FULL_TRACK_PROFILES = (
    "single_target_range25_v1",
    "single_target_az20_range25_v1",
    "single_target_vel3_range25_v1",
    "dual_target_split_range25_v1",
    "single_target_material_loss_range25_v1",
    "mesh_dihedral_range25_v1",
    "mesh_trihedral_range25_v1",
)
DEFAULT_GATE_FAMILIES = ("equivalence_strict",)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run PO-SBR physical full-track validation bundle using backend scenario matrix "
            "and emit one readiness report for radar-developer workflows."
        )
    )
    p.add_argument("--output-root", required=True, help="Output root directory for full-track artifacts")
    p.add_argument("--output-summary-json", required=True, help="Output full-track summary JSON path")
    p.add_argument(
        "--matrix-summary-json",
        default=None,
        help="Optional matrix summary JSON path (default: <output-root>/scene_backend_kpi_scenario_matrix.json)",
    )
    p.add_argument(
        "--profile",
        action="append",
        default=[],
        help="Profile id to include (repeatable, comma-separated allowed).",
    )
    p.add_argument(
        "--gate-profile-family",
        action="append",
        default=[],
        help="Gate profile family (repeatable, comma-separated allowed). Default: equivalence_strict",
    )
    p.add_argument("--n-chirps", type=int, default=8, help="Chirps per profile run")
    p.add_argument("--samples-per-chirp", type=int, default=1024, help="Samples per chirp")
    p.add_argument(
        "--strict-ready",
        action="store_true",
        help="Exit non-zero unless full_track_status=ready",
    )
    p.add_argument(
        "--python-bin",
        default=str(sys.executable),
        help="Python interpreter used for subprocess runner calls",
    )
    p.add_argument("--sionna-runtime-provider", default=None, help="Optional sionna runtime provider override")
    p.add_argument(
        "--sionna-runtime-required-modules",
        default=None,
        help="Optional sionna required modules CSV override",
    )
    p.add_argument("--po-sbr-runtime-provider", default=None, help="Optional PO-SBR runtime provider override")
    p.add_argument(
        "--po-sbr-runtime-required-modules",
        default=None,
        help="Optional PO-SBR required modules CSV override",
    )
    p.add_argument("--po-sbr-repo-root", default=None, help="Optional PO-SBR repo root override")
    p.add_argument("--po-sbr-geometry-path", default=None, help="Optional PO-SBR geometry path override")
    return p.parse_args()


def _parse_csv_list(items: Sequence[str], default_values: Sequence[str]) -> List[str]:
    if len(items) == 0:
        return [str(x) for x in default_values]
    out: List[str] = []
    for raw in items:
        for token in str(raw).split(","):
            text = str(token).strip()
            if text == "":
                continue
            if text not in out:
                out.append(text)
    if len(out) == 0:
        raise ValueError("at least one item must be selected")
    return out


def _run_cmd(cmd: List[str], cwd: Path) -> Dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    return {
        "ok": bool(proc.returncode == 0),
        "return_code": int(proc.returncode),
        "stdout": str(proc.stdout).strip(),
        "stderr": str(proc.stderr).strip(),
        "cmd": cmd,
    }


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _build_optional_matrix_overrides(args: argparse.Namespace) -> List[str]:
    out: List[str] = []

    def add_opt(flag: str, value: Any, allow_empty: bool = False) -> None:
        if value is None:
            return
        raw_text = str(value)
        text = raw_text.strip()
        if (not allow_empty) and text == "":
            return
        out.extend([flag, raw_text if allow_empty else text])

    add_opt("--sionna-runtime-provider", args.sionna_runtime_provider)
    add_opt("--sionna-runtime-required-modules", args.sionna_runtime_required_modules, allow_empty=True)
    add_opt("--po-sbr-runtime-provider", args.po_sbr_runtime_provider)
    add_opt("--po-sbr-runtime-required-modules", args.po_sbr_runtime_required_modules, allow_empty=True)
    add_opt("--po-sbr-repo-root", args.po_sbr_repo_root)
    add_opt("--po-sbr-geometry-path", args.po_sbr_geometry_path)
    return out


def _extract_po_sbr_row_details(golden_summary_json: Path) -> Dict[str, Any]:
    if not golden_summary_json.exists():
        return {
            "po_sbr_status": None,
            "po_sbr_path_count": None,
            "po_sbr_scene_json": None,
            "po_sbr_geometry_path": None,
        }
    payload = _load_json(golden_summary_json)
    results = payload.get("results")
    if not isinstance(results, Mapping):
        return {
            "po_sbr_status": None,
            "po_sbr_path_count": None,
            "po_sbr_scene_json": None,
            "po_sbr_geometry_path": None,
        }
    po = dict(results.get("po_sbr_rt") or {})
    scene_json_text = str(po.get("scene_json", "")).strip()
    scene_json_path = None
    if scene_json_text != "":
        scene_json_path = Path(scene_json_text)
    geometry_path = None
    if scene_json_path is not None and scene_json_path.exists():
        try:
            scene_payload = _load_json(scene_json_path)
            backend = scene_payload.get("backend")
            if isinstance(backend, Mapping):
                runtime_input = backend.get("runtime_input")
                if isinstance(runtime_input, Mapping):
                    geom_text = str(runtime_input.get("geometry_path", "")).strip()
                    if geom_text != "":
                        geometry_path = geom_text
        except Exception:
            geometry_path = None
    return {
        "po_sbr_status": str(po.get("status", "")).strip() or None,
        "po_sbr_path_count": int(po.get("path_count", 0)) if po.get("path_count") is not None else None,
        "po_sbr_scene_json": str(scene_json_path) if scene_json_path is not None else None,
        "po_sbr_geometry_path": geometry_path,
    }


def _default_po_sbr_row_details() -> Dict[str, Any]:
    return {
        "po_sbr_status": None,
        "po_sbr_path_count": None,
        "po_sbr_scene_json": None,
        "po_sbr_geometry_path": None,
    }


def main() -> None:
    args = parse_args()
    profiles = _parse_csv_list(args.profile, DEFAULT_FULL_TRACK_PROFILES)
    gate_families = _parse_csv_list(args.gate_profile_family, DEFAULT_GATE_FAMILIES)

    if int(args.n_chirps) <= 0:
        raise ValueError("--n-chirps must be > 0")
    if int(args.samples_per_chirp) <= 0:
        raise ValueError("--samples-per-chirp must be > 0")

    cwd = Path.cwd().resolve()
    output_root = Path(args.output_root).expanduser()
    if not output_root.is_absolute():
        output_root = (cwd / output_root).resolve()
    else:
        output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    output_summary_json = Path(args.output_summary_json).expanduser()
    if not output_summary_json.is_absolute():
        output_summary_json = (cwd / output_summary_json).resolve()
    else:
        output_summary_json = output_summary_json.resolve()
    output_summary_json.parent.mkdir(parents=True, exist_ok=True)

    if args.matrix_summary_json is None:
        matrix_summary_json = output_root / "scene_backend_kpi_scenario_matrix.json"
    else:
        matrix_summary_json = Path(args.matrix_summary_json).expanduser()
        if not matrix_summary_json.is_absolute():
            matrix_summary_json = (cwd / matrix_summary_json).resolve()
        else:
            matrix_summary_json = matrix_summary_json.resolve()
    matrix_summary_json.parent.mkdir(parents=True, exist_ok=True)

    matrix_output_root = output_root / "matrix_runs"
    matrix_output_root.mkdir(parents=True, exist_ok=True)

    python_path = Path(str(args.python_bin)).expanduser()
    if not python_path.is_absolute():
        python_path = (cwd / python_path).resolve()
    python_bin = str(python_path)

    matrix_cmd: List[str] = [
        python_bin,
        "scripts/run_scene_backend_kpi_scenario_matrix.py",
        "--output-root",
        str(matrix_output_root),
        "--output-summary-json",
        str(matrix_summary_json),
        "--n-chirps",
        str(int(args.n_chirps)),
        "--samples-per-chirp",
        str(int(args.samples_per_chirp)),
    ]
    for profile in profiles:
        matrix_cmd.extend(["--profile", profile])
    for family in gate_families:
        matrix_cmd.extend(["--gate-profile-family", family])
    matrix_cmd.extend(_build_optional_matrix_overrides(args))

    matrix_run = _run_cmd(matrix_cmd, cwd=cwd)
    matrix_payload: Optional[Dict[str, Any]] = None
    if matrix_summary_json.exists():
        matrix_payload = _load_json(matrix_summary_json)

    rows: List[Dict[str, Any]] = []
    matrix_rows = []
    if isinstance(matrix_payload, Mapping):
        raw_rows = matrix_payload.get("rows")
        if isinstance(raw_rows, list):
            matrix_rows = raw_rows
    row_by_profile: Dict[str, Dict[str, Any]] = {}
    for row in matrix_rows:
        if not isinstance(row, Mapping):
            continue
        profile = str(row.get("profile", "")).strip()
        if profile == "":
            continue
        row_by_profile[profile] = dict(row)

    missing_profiles = [profile for profile in profiles if profile not in row_by_profile]
    for profile in profiles:
        row = dict(row_by_profile.get(profile) or {})
        golden_json_text = str(row.get("golden_summary_json", "")).strip()
        golden_json = Path(golden_json_text) if golden_json_text != "" else None
        po_sbr_detail = (
            _extract_po_sbr_row_details(golden_json)
            if golden_json is not None
            else _default_po_sbr_row_details()
        )
        rows.append(
            {
                "profile": profile,
                "profile_family": str(row.get("profile_family", "")).strip() or None,
                "gate_required": bool(row.get("gate_required", False)),
                "run_ok": bool(row.get("run_ok", False)),
                "campaign_status": str(row.get("campaign_status", "")).strip() or None,
                "parity_fail_count": (
                    int(row.get("parity_fail_count", 0))
                    if row.get("parity_fail_count") is not None
                    else None
                ),
                "golden_summary_json": str(golden_json) if golden_json is not None else None,
                "kpi_summary_json": str(row.get("kpi_summary_json", "")).strip() or None,
                "po_sbr_status": po_sbr_detail["po_sbr_status"],
                "po_sbr_path_count": po_sbr_detail["po_sbr_path_count"],
                "po_sbr_scene_json": po_sbr_detail["po_sbr_scene_json"],
                "po_sbr_geometry_path": po_sbr_detail["po_sbr_geometry_path"],
            }
        )

    matrix_status = None
    matrix_summary = {}
    if isinstance(matrix_payload, Mapping):
        matrix_status = str(matrix_payload.get("matrix_status", "")).strip() or None
        summary_raw = matrix_payload.get("summary")
        if isinstance(summary_raw, Mapping):
            matrix_summary = dict(summary_raw)

    blockers: List[str] = []
    if not bool(matrix_run.get("ok", False)):
        blockers.append("matrix_runner_failed")
    if len(missing_profiles) > 0:
        blockers.append("missing_required_profiles")
    if matrix_status != "ready":
        blockers.append("matrix_status_not_ready")
    if int(matrix_summary.get("failed_profile_count", 0)) > 0:
        blockers.append("matrix_profile_failures_detected")
    if int(matrix_summary.get("gate_blocked_profile_count", 0)) > 0:
        blockers.append("gate_profiles_blocked")

    full_track_status = "ready" if len(blockers) == 0 else "blocked"
    po_sbr_executed_count = int(sum(1 for row in rows if str(row.get("po_sbr_status", "")) == "executed"))

    report = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "workspace_root": str(cwd),
        "python_executable": str(Path(sys.executable).resolve()),
        "purpose": "AVX-like radar simulation physical full-track PO-SBR readiness bundle",
        "required_profiles": profiles,
        "gate_profile_families": gate_families,
        "missing_required_profiles": missing_profiles,
        "full_track_status": full_track_status,
        "blockers": blockers,
        "source_matrix_summary_json": str(matrix_summary_json),
        "matrix_status": matrix_status,
        "matrix_summary": matrix_summary,
        "matrix_run": matrix_run,
        "rows": rows,
        "summary": {
            "required_profile_count": int(len(profiles)),
            "present_profile_count": int(len(profiles) - len(missing_profiles)),
            "missing_profile_count": int(len(missing_profiles)),
            "po_sbr_executed_profile_count": po_sbr_executed_count,
            "gate_blocked_profile_count": int(matrix_summary.get("gate_blocked_profile_count", 0)),
            "informational_blocked_profile_count": int(
                matrix_summary.get("informational_blocked_profile_count", 0)
            ),
        },
    }
    output_summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("PO-SBR physical full-track bundle completed.")
    print(f"  full_track_status: {full_track_status}")
    print(f"  blockers: {blockers}")
    print(f"  matrix_status: {matrix_status}")
    print(f"  required_profile_count: {len(profiles)}")
    print(f"  missing_profile_count: {len(missing_profiles)}")
    print(f"  output_summary_json: {output_summary_json}")

    if bool(args.strict_ready) and full_track_status != "ready":
        raise RuntimeError("physical full-track bundle is not ready")


if __name__ == "__main__":
    main()
