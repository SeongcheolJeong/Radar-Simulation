#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


DEFAULT_BUNDLE_SUMMARY_JSON = "docs/reports/po_sbr_physical_full_track_bundle_local_2026_03_01.json"
DEFAULT_REALISM_GATE_CANDIDATE = "realism_tight_v2"
REQUIRED_BACKENDS_CSV = "analytic_targets,sionna_rt,po_sbr_rt"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y_%m_%d_%H%M%S")


def parse_args() -> argparse.Namespace:
    stamp = _utc_stamp()
    p = argparse.ArgumentParser(
        description=(
            "Run one-command local PO-SBR readiness regression on this PC: "
            "scene backend golden-path + KPI campaign + scenario matrix + full-track gate lock."
        )
    )
    p.add_argument(
        "--output-root",
        default=f"data/runtime_golden_path/po_sbr_local_ready_regression_{stamp}",
        help="Output root directory for generated artifacts",
    )
    p.add_argument(
        "--output-summary-json",
        default=f"docs/reports/po_sbr_local_ready_regression_{stamp}.json",
        help="Output summary JSON path for this orchestrated run",
    )
    p.add_argument(
        "--full-track-bundle-summary-json",
        default=DEFAULT_BUNDLE_SUMMARY_JSON,
        help=(
            "Input summary JSON from scripts/run_po_sbr_physical_full_track_bundle.py "
            f"(default: {DEFAULT_BUNDLE_SUMMARY_JSON})"
        ),
    )
    p.add_argument(
        "--reuse-stability-summary-json",
        default=None,
        help="Optional reuse summary JSON for gate-lock stability phase",
    )
    p.add_argument(
        "--reuse-hardening-summary-json",
        default=None,
        help="Optional reuse summary JSON for gate-lock hardening phase",
    )
    p.add_argument("--n-chirps", type=int, default=8, help="Chirps per run")
    p.add_argument("--samples-per-chirp", type=int, default=1024, help="Samples per chirp")
    p.add_argument(
        "--stability-runs",
        type=int,
        default=3,
        help="Gate-lock stability run count",
    )
    p.add_argument(
        "--threshold-profile",
        action="append",
        default=[],
        help=(
            "Gate-lock hardening threshold profile id (repeatable, comma-separated allowed). "
            "Default: realism gate candidate only"
        ),
    )
    p.add_argument(
        "--realism-gate-candidate",
        default=DEFAULT_REALISM_GATE_CANDIDATE,
        help=f"Gate-lock realism candidate profile (default: {DEFAULT_REALISM_GATE_CANDIDATE})",
    )
    p.add_argument(
        "--matrix-profile",
        action="append",
        default=[],
        help="Scenario matrix profile id (repeatable, comma-separated allowed). Default: script built-ins",
    )
    p.add_argument(
        "--strict-ready",
        action="store_true",
        help="Exit non-zero unless overall_status=ready",
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


def _resolve_path(raw_path: str, cwd: Path) -> Path:
    path = Path(str(raw_path)).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (cwd / path).resolve()


def _run_cmd(cmd: List[str], cwd: Path) -> Dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    return {
        "ok": bool(proc.returncode == 0),
        "return_code": int(proc.returncode),
        "stdout": str(proc.stdout).strip(),
        "stderr": str(proc.stderr).strip(),
        "cmd": list(cmd),
    }


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _parse_csv_items(items: Sequence[str]) -> List[str]:
    out: List[str] = []
    for raw in items:
        for token in str(raw).split(","):
            text = str(token).strip()
            if text == "":
                continue
            if text not in out:
                out.append(text)
    return out


def _build_optional_runtime_overrides(args: argparse.Namespace) -> List[str]:
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


def _summary_status(payload: Optional[Mapping[str, Any]], key: str) -> Optional[str]:
    if not isinstance(payload, Mapping):
        return None
    value = str(payload.get(key, "")).strip()
    return value or None


def _write_report(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if int(args.n_chirps) <= 0:
        raise ValueError("--n-chirps must be > 0")
    if int(args.samples_per_chirp) <= 0:
        raise ValueError("--samples-per-chirp must be > 0")
    if int(args.stability_runs) <= 0:
        raise ValueError("--stability-runs must be > 0")

    realism_gate_candidate = str(args.realism_gate_candidate).strip()
    if realism_gate_candidate == "":
        raise ValueError("--realism-gate-candidate must be non-empty")

    threshold_profiles = _parse_csv_items(args.threshold_profile)
    if len(threshold_profiles) == 0:
        threshold_profiles = [realism_gate_candidate]
    if realism_gate_candidate not in threshold_profiles:
        threshold_profiles.append(realism_gate_candidate)

    matrix_profiles = _parse_csv_items(args.matrix_profile)

    cwd = Path.cwd().resolve()
    output_root = _resolve_path(args.output_root, cwd=cwd)
    output_root.mkdir(parents=True, exist_ok=True)
    output_summary_json = _resolve_path(args.output_summary_json, cwd=cwd)
    output_summary_json.parent.mkdir(parents=True, exist_ok=True)

    full_track_bundle_summary_json = _resolve_path(args.full_track_bundle_summary_json, cwd=cwd)
    if not full_track_bundle_summary_json.exists():
        raise FileNotFoundError(f"full-track bundle summary not found: {full_track_bundle_summary_json}")

    python_path = Path(str(args.python_bin)).expanduser()
    if not python_path.is_absolute():
        python_path = (cwd / python_path).resolve()
    python_bin = str(python_path)

    runtime_overrides = _build_optional_runtime_overrides(args=args)

    golden_root = output_root / "scene_backend_golden_path"
    golden_summary_json = output_root / "scene_backend_golden_path.json"
    run_golden = _run_cmd(
        [
            python_bin,
            "scripts/run_scene_backend_golden_path.py",
            "--strict-nonexecuted",
            "--n-chirps",
            str(int(args.n_chirps)),
            "--samples-per-chirp",
            str(int(args.samples_per_chirp)),
            "--output-root",
            str(golden_root),
            "--output-summary-json",
            str(golden_summary_json),
            *runtime_overrides,
        ],
        cwd=cwd,
    )
    validate_golden = _run_cmd(
        [
            python_bin,
            "scripts/validate_scene_backend_golden_path_report.py",
            "--summary-json",
            str(golden_summary_json),
            "--require-backend-executed",
            REQUIRED_BACKENDS_CSV,
        ],
        cwd=cwd,
    )
    golden_payload = _load_json(golden_summary_json)
    golden_summary = _mapping((golden_payload or {}).get("summary"))
    golden_migration_status = str(golden_summary.get("po_sbr_migration_status", "")).strip()
    golden_executed_count = int(golden_summary.get("executed_count", 0) or 0)
    golden_requested_count = int(golden_summary.get("requested_count", 0) or 0)
    golden_status = (
        "ready"
        if run_golden.get("ok", False)
        and validate_golden.get("ok", False)
        and golden_migration_status == "closed_local_runtime"
        and golden_executed_count == golden_requested_count
        else "blocked"
    )

    kpi_summary_json = output_root / "scene_backend_kpi_campaign.json"
    run_kpi = _run_cmd(
        [
            python_bin,
            "scripts/run_scene_backend_kpi_campaign.py",
            "--golden-path-summary-json",
            str(golden_summary_json),
            "--output-summary-json",
            str(kpi_summary_json),
            "--strict-ready",
        ],
        cwd=cwd,
    )
    validate_kpi = _run_cmd(
        [
            python_bin,
            "scripts/validate_scene_backend_kpi_campaign_report.py",
            "--summary-json",
            str(kpi_summary_json),
            "--require-ready",
        ],
        cwd=cwd,
    )
    kpi_payload = _load_json(kpi_summary_json)
    kpi_summary = _mapping((kpi_payload or {}).get("summary"))
    kpi_campaign_status = _summary_status(kpi_payload, "campaign_status")
    kpi_parity_fail_count = int(kpi_summary.get("parity_fail_count", 0) or 0)
    kpi_status = (
        "ready"
        if run_kpi.get("ok", False)
        and validate_kpi.get("ok", False)
        and kpi_campaign_status == "ready"
        and kpi_parity_fail_count == 0
        else "blocked"
    )

    matrix_root = output_root / "scene_backend_kpi_scenario_matrix"
    matrix_summary_json = output_root / "scene_backend_kpi_scenario_matrix.json"
    run_matrix_cmd = [
        python_bin,
        "scripts/run_scene_backend_kpi_scenario_matrix.py",
        "--output-root",
        str(matrix_root),
        "--output-summary-json",
        str(matrix_summary_json),
        "--n-chirps",
        str(int(args.n_chirps)),
        "--samples-per-chirp",
        str(int(args.samples_per_chirp)),
        "--strict-all-ready",
        *runtime_overrides,
    ]
    for profile in matrix_profiles:
        run_matrix_cmd.extend(["--profile", profile])
    run_matrix = _run_cmd(run_matrix_cmd, cwd=cwd)
    validate_matrix = _run_cmd(
        [
            python_bin,
            "scripts/validate_scene_backend_kpi_scenario_matrix_report.py",
            "--summary-json",
            str(matrix_summary_json),
            "--require-ready",
        ],
        cwd=cwd,
    )
    matrix_payload = _load_json(matrix_summary_json)
    matrix_summary = _mapping((matrix_payload or {}).get("summary"))
    matrix_status_value = _summary_status(matrix_payload, "matrix_status")
    matrix_profile_count = int(matrix_summary.get("profile_count", 0) or 0)
    matrix_blocked_count = int(matrix_summary.get("blocked_profile_count", 0) or 0)
    matrix_failed_count = int(matrix_summary.get("failed_profile_count", 0) or 0)
    matrix_status = (
        "ready"
        if run_matrix.get("ok", False)
        and validate_matrix.get("ok", False)
        and matrix_status_value == "ready"
        and matrix_profile_count > 0
        and matrix_blocked_count == 0
        and matrix_failed_count == 0
        else "blocked"
    )

    gate_lock_root = output_root / "po_sbr_physical_full_track_gate_lock"
    gate_lock_summary_json = output_root / "po_sbr_physical_full_track_gate_lock.json"
    run_gate_lock_cmd = [
        python_bin,
        "scripts/run_po_sbr_physical_full_track_gate_lock.py",
        "--strict-ready",
        "--full-track-bundle-summary-json",
        str(full_track_bundle_summary_json),
        "--output-root",
        str(gate_lock_root),
        "--output-summary-json",
        str(gate_lock_summary_json),
        "--stability-runs",
        str(int(args.stability_runs)),
        "--n-chirps",
        str(int(args.n_chirps)),
        "--samples-per-chirp",
        str(int(args.samples_per_chirp)),
        "--realism-gate-candidate",
        realism_gate_candidate,
        *runtime_overrides,
    ]
    for profile in threshold_profiles:
        run_gate_lock_cmd.extend(["--threshold-profile", profile])
    if args.reuse_stability_summary_json is not None:
        reuse_stability_summary_json = _resolve_path(args.reuse_stability_summary_json, cwd=cwd)
        run_gate_lock_cmd.extend(["--reuse-stability-summary-json", str(reuse_stability_summary_json)])
    if args.reuse_hardening_summary_json is not None:
        reuse_hardening_summary_json = _resolve_path(args.reuse_hardening_summary_json, cwd=cwd)
        run_gate_lock_cmd.extend(["--reuse-hardening-summary-json", str(reuse_hardening_summary_json)])
    run_gate_lock = _run_cmd(run_gate_lock_cmd, cwd=cwd)

    validate_gate_lock = _run_cmd(
        [
            python_bin,
            "scripts/validate_po_sbr_physical_full_track_gate_lock_report.py",
            "--summary-json",
            str(gate_lock_summary_json),
            "--require-ready",
        ],
        cwd=cwd,
    )

    gate_lock_payload = _load_json(gate_lock_summary_json)
    gate_lock_summary = _mapping((gate_lock_payload or {}).get("summary"))
    gate_lock_status_value = _summary_status(gate_lock_payload, "gate_lock_status")
    gate_lock_stability_status = str(gate_lock_summary.get("stability_status", "")).strip()
    gate_lock_hardening_status = str(gate_lock_summary.get("hardening_status", "")).strip()
    gate_lock_candidate_status = str(gate_lock_summary.get("realism_gate_candidate_status", "")).strip()
    stability_raw = str(_mapping((gate_lock_payload or {}).get("stability")).get("summary_json", "")).strip()
    hardening_raw = str(_mapping((gate_lock_payload or {}).get("hardening")).get("summary_json", "")).strip()
    gate_lock_stability_json = _resolve_path(stability_raw, cwd=cwd) if stability_raw != "" else Path("")
    gate_lock_hardening_json = _resolve_path(hardening_raw, cwd=cwd) if hardening_raw != "" else Path("")

    if stability_raw == "":
        validate_stability = {
            "ok": False,
            "return_code": 2,
            "stdout": "",
            "stderr": "missing_stability_summary_json",
            "cmd": ["missing", "stability_summary_json"],
        }
    else:
        validate_stability = _run_cmd(
            [
                python_bin,
                "scripts/validate_po_sbr_physical_full_track_stability_report.py",
                "--summary-json",
                str(gate_lock_stability_json),
                "--require-stable",
            ],
            cwd=cwd,
        )

    if hardening_raw == "":
        validate_hardening = {
            "ok": False,
            "return_code": 2,
            "stdout": "",
            "stderr": "missing_hardening_summary_json",
            "cmd": ["missing", "hardening_summary_json"],
        }
    else:
        validate_hardening = _run_cmd(
            [
                python_bin,
                "scripts/validate_po_sbr_realism_threshold_hardening_report.py",
                "--summary-json",
                str(gate_lock_hardening_json),
                "--require-hardened",
            ],
            cwd=cwd,
        )

    gate_lock_status = (
        "ready"
        if run_gate_lock.get("ok", False)
        and validate_gate_lock.get("ok", False)
        and validate_stability.get("ok", False)
        and validate_hardening.get("ok", False)
        and gate_lock_status_value == "ready"
        and gate_lock_stability_status == "stable"
        and gate_lock_hardening_status == "hardened"
        and gate_lock_candidate_status == "ready"
        else "blocked"
    )

    blockers: List[str] = []
    if golden_status != "ready":
        blockers.append("scene_backend_golden_path_not_ready")
    if kpi_status != "ready":
        blockers.append("scene_backend_kpi_campaign_not_ready")
    if matrix_status != "ready":
        blockers.append("scene_backend_kpi_scenario_matrix_not_ready")
    if gate_lock_status != "ready":
        blockers.append("po_sbr_full_track_gate_lock_not_ready")

    run_steps = [
        ("run_golden", run_golden),
        ("validate_golden", validate_golden),
        ("run_kpi", run_kpi),
        ("validate_kpi", validate_kpi),
        ("run_matrix", run_matrix),
        ("validate_matrix", validate_matrix),
        ("run_gate_lock", run_gate_lock),
        ("validate_gate_lock", validate_gate_lock),
        ("validate_stability", validate_stability),
        ("validate_hardening", validate_hardening),
    ]
    failed_steps = [name for (name, step) in run_steps if not bool(step.get("ok", False))]

    if len(failed_steps) > 0:
        overall_status = "failed"
    elif len(blockers) > 0:
        overall_status = "blocked"
    else:
        overall_status = "ready"

    report = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(cwd),
        "python_executable": python_bin,
        "output_root": str(output_root),
        "full_track_bundle_summary_json": str(full_track_bundle_summary_json),
        "failed_steps": failed_steps,
        "blockers": blockers,
        "reports": {
            "golden_path": {
                "summary_json": str(golden_summary_json),
                "run": run_golden,
                "validate": validate_golden,
                "migration_status": golden_migration_status,
                "executed_count": golden_executed_count,
                "requested_count": golden_requested_count,
                "status": golden_status,
                "summary": golden_summary,
            },
            "kpi_campaign": {
                "summary_json": str(kpi_summary_json),
                "run": run_kpi,
                "validate": validate_kpi,
                "campaign_status": kpi_campaign_status,
                "parity_fail_count": kpi_parity_fail_count,
                "status": kpi_status,
                "summary": kpi_summary,
            },
            "kpi_scenario_matrix": {
                "summary_json": str(matrix_summary_json),
                "run": run_matrix,
                "validate": validate_matrix,
                "matrix_status": matrix_status_value,
                "profile_count": matrix_profile_count,
                "blocked_profile_count": matrix_blocked_count,
                "failed_profile_count": matrix_failed_count,
                "status": matrix_status,
                "summary": matrix_summary,
            },
            "gate_lock": {
                "summary_json": str(gate_lock_summary_json),
                "stability_summary_json": str(gate_lock_stability_json) if stability_raw != "" else "",
                "hardening_summary_json": str(gate_lock_hardening_json) if hardening_raw != "" else "",
                "run": run_gate_lock,
                "validate_gate_lock": validate_gate_lock,
                "validate_stability": validate_stability,
                "validate_hardening": validate_hardening,
                "gate_lock_status": gate_lock_status_value,
                "stability_status": gate_lock_stability_status,
                "hardening_status": gate_lock_hardening_status,
                "realism_gate_candidate_status": gate_lock_candidate_status,
                "status": gate_lock_status,
                "summary": gate_lock_summary,
            },
        },
        "summary": {
            "golden_path_status": golden_status,
            "kpi_campaign_status": kpi_status,
            "kpi_scenario_matrix_status": matrix_status,
            "gate_lock_status": gate_lock_status,
            "overall_status": overall_status,
        },
    }
    _write_report(output_summary_json, report)

    print("PO-SBR local readiness regression completed.")
    print(f"  overall_status: {overall_status}")
    print(f"  failed_steps: {failed_steps}")
    print(f"  blockers: {blockers}")
    print(f"  golden_path_status: {golden_status}")
    print(f"  kpi_campaign_status: {kpi_status}")
    print(f"  kpi_scenario_matrix_status: {matrix_status}")
    print(f"  gate_lock_status: {gate_lock_status}")
    print(f"  output_summary_json: {output_summary_json}")

    if bool(args.strict_ready) and overall_status != "ready":
        raise RuntimeError(f"local readiness regression is not ready: {overall_status}")


if __name__ == "__main__":
    main()
