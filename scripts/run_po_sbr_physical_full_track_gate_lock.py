#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


DEFAULT_REALISM_GATE_CANDIDATE = "realism_tight_v2"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run local PO-SBR full-track gate lock in one command: repeated stability campaign "
            "+ realism threshold hardening candidate lock."
        )
    )
    p.add_argument(
        "--full-track-bundle-summary-json",
        required=True,
        help="Input summary JSON from scripts/run_po_sbr_physical_full_track_bundle.py",
    )
    p.add_argument("--output-root", required=True, help="Output root directory for gate-lock artifacts")
    p.add_argument("--output-summary-json", required=True, help="Output gate-lock summary JSON path")
    p.add_argument(
        "--reuse-stability-summary-json",
        default=None,
        help="Reuse existing stability summary JSON and skip stability runner execution",
    )
    p.add_argument(
        "--reuse-hardening-summary-json",
        default=None,
        help="Reuse existing hardening summary JSON and skip hardening runner execution",
    )
    p.add_argument(
        "--stability-runs",
        type=int,
        default=3,
        help="Number of repeated full-track runs in stability phase (default: 3)",
    )
    p.add_argument("--n-chirps", type=int, default=8, help="Chirps per profile run")
    p.add_argument("--samples-per-chirp", type=int, default=1024, help="Samples per chirp")
    p.add_argument(
        "--threshold-profile",
        action="append",
        default=[],
        help=(
            "Threshold profile id for hardening phase (repeatable, comma-separated allowed). "
            "Default: realism gate candidate only"
        ),
    )
    p.add_argument(
        "--realism-gate-candidate",
        default=DEFAULT_REALISM_GATE_CANDIDATE,
        help=f"Realism threshold profile promoted as gate candidate (default: {DEFAULT_REALISM_GATE_CANDIDATE})",
    )
    p.add_argument(
        "--strict-ready",
        action="store_true",
        help="Exit non-zero unless gate_lock_status=ready",
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


def _resolve_path(raw_path: str, cwd: Path) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (cwd / path).resolve()


def _parse_threshold_profiles(items: Sequence[str], candidate: str) -> List[str]:
    out: List[str] = []
    for raw in items:
        for token in str(raw).split(","):
            profile = str(token).strip()
            if profile == "":
                continue
            if profile not in out:
                out.append(profile)
    if len(out) == 0:
        out.append(candidate)
    if candidate not in out:
        out.append(candidate)
    return out


def _build_optional_bundle_overrides(args: argparse.Namespace) -> List[str]:
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


def _load_summary_status(path: Path, status_key: str) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
    if not path.exists():
        return None, None
    payload = _load_json(path)
    summary_payload = payload.get("summary")
    summary: Optional[Dict[str, Any]] = None
    if isinstance(summary_payload, Mapping):
        summary = dict(summary_payload)
    status = str(payload.get(status_key, "")).strip() or None
    return status, summary


def main() -> None:
    args = parse_args()
    if int(args.stability_runs) <= 0:
        raise ValueError("--stability-runs must be > 0")
    if int(args.n_chirps) <= 0:
        raise ValueError("--n-chirps must be > 0")
    if int(args.samples_per_chirp) <= 0:
        raise ValueError("--samples-per-chirp must be > 0")

    realism_gate_candidate = str(args.realism_gate_candidate).strip()
    if realism_gate_candidate == "":
        raise ValueError("--realism-gate-candidate must be non-empty")
    threshold_profiles = _parse_threshold_profiles(args.threshold_profile, candidate=realism_gate_candidate)

    cwd = Path.cwd().resolve()
    output_root = _resolve_path(args.output_root, cwd=cwd)
    output_root.mkdir(parents=True, exist_ok=True)

    output_summary_json = _resolve_path(args.output_summary_json, cwd=cwd)
    output_summary_json.parent.mkdir(parents=True, exist_ok=True)

    full_track_summary_json = _resolve_path(args.full_track_bundle_summary_json, cwd=cwd)
    if not full_track_summary_json.exists():
        raise FileNotFoundError(f"full-track bundle summary not found: {full_track_summary_json}")

    python_path = Path(str(args.python_bin)).expanduser()
    if not python_path.is_absolute():
        python_path = (cwd / python_path).resolve()
    # Keep absolute interpreter path without resolving symlinks so venv launchers stay active.
    python_bin = str(python_path)
    bundle_overrides = _build_optional_bundle_overrides(args=args)

    reuse_stability_summary_json = None
    if args.reuse_stability_summary_json is not None:
        reuse_stability_summary_json = _resolve_path(args.reuse_stability_summary_json, cwd=cwd)
        if not reuse_stability_summary_json.exists():
            raise FileNotFoundError(f"reused stability summary not found: {reuse_stability_summary_json}")

    stability_root = output_root / "stability_campaign"
    stability_root.mkdir(parents=True, exist_ok=True)
    stability_summary_json = (
        reuse_stability_summary_json
        if reuse_stability_summary_json is not None
        else (stability_root / "po_sbr_physical_full_track_stability.json")
    )

    if reuse_stability_summary_json is not None:
        run_stability = {
            "ok": True,
            "return_code": 0,
            "stdout": "reused_existing_stability_summary",
            "stderr": "",
            "cmd": ["reuse", str(stability_summary_json)],
        }
    else:
        run_stability = _run_cmd(
            [
                python_bin,
                "scripts/run_po_sbr_physical_full_track_stability_campaign.py",
                "--output-root",
                str(stability_root / "campaign_outputs"),
                "--output-summary-json",
                str(stability_summary_json),
                "--runs",
                str(int(args.stability_runs)),
                "--n-chirps",
                str(int(args.n_chirps)),
                "--samples-per-chirp",
                str(int(args.samples_per_chirp)),
                *bundle_overrides,
            ],
            cwd=cwd,
        )
    stability_status, stability_summary = _load_summary_status(
        path=stability_summary_json,
        status_key="campaign_status",
    )

    reuse_hardening_summary_json = None
    if args.reuse_hardening_summary_json is not None:
        reuse_hardening_summary_json = _resolve_path(args.reuse_hardening_summary_json, cwd=cwd)
        if not reuse_hardening_summary_json.exists():
            raise FileNotFoundError(f"reused hardening summary not found: {reuse_hardening_summary_json}")

    hardening_root = output_root / "hardening_campaign"
    hardening_root.mkdir(parents=True, exist_ok=True)
    hardening_summary_json = (
        reuse_hardening_summary_json
        if reuse_hardening_summary_json is not None
        else (hardening_root / "po_sbr_realism_threshold_hardening.json")
    )

    if reuse_hardening_summary_json is not None:
        run_hardening = {
            "ok": True,
            "return_code": 0,
            "stdout": "reused_existing_hardening_summary",
            "stderr": "",
            "cmd": ["reuse", str(hardening_summary_json)],
        }
    else:
        hardening_cmd = [
            python_bin,
            "scripts/run_po_sbr_realism_threshold_hardening_campaign.py",
            "--full-track-bundle-summary-json",
            str(full_track_summary_json),
            "--stability-summary-json",
            str(stability_summary_json),
            "--output-root",
            str(hardening_root / "campaign_outputs"),
            "--output-summary-json",
            str(hardening_summary_json),
            "--realism-gate-candidate",
            realism_gate_candidate,
        ]
        for profile in threshold_profiles:
            hardening_cmd.extend(["--threshold-profile", profile])
        run_hardening = _run_cmd(hardening_cmd, cwd=cwd)
    hardening_status, hardening_summary = _load_summary_status(
        path=hardening_summary_json,
        status_key="hardening_status",
    )

    hardening_payload: Optional[Dict[str, Any]] = None
    hardening_candidate = None
    hardening_candidate_status = None
    if hardening_summary_json.exists():
        hardening_payload = _load_json(hardening_summary_json)
        hardening_candidate = str(hardening_payload.get("realism_gate_candidate", "")).strip() or None
        hardening_candidate_status = (
            str(hardening_payload.get("realism_gate_candidate_status", "")).strip() or None
        )

    blockers: List[str] = []
    if not bool(run_stability.get("ok", False)):
        blockers.append("stability_runner_failed")
    if stability_status != "stable":
        blockers.append("stability_campaign_not_stable")
    if not bool(run_hardening.get("ok", False)):
        blockers.append("hardening_runner_failed")
    if hardening_status != "hardened":
        blockers.append("hardening_campaign_not_hardened")
    if hardening_candidate is None:
        blockers.append("hardening_candidate_missing")
    elif hardening_candidate != realism_gate_candidate:
        blockers.append("hardening_candidate_mismatch")
    if hardening_candidate_status != "ready":
        blockers.append("realism_gate_candidate_not_ready")

    gate_lock_status = "ready" if len(blockers) == 0 else "blocked"
    report = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "workspace_root": str(cwd),
        "python_executable": str(Path(sys.executable).resolve()),
        "gate_lock_status": gate_lock_status,
        "blockers": blockers,
        "full_track_bundle_summary_json": str(full_track_summary_json),
        "realism_gate_candidate": realism_gate_candidate,
        "threshold_profiles": threshold_profiles,
        "stability": {
            "run": run_stability,
            "summary_json": str(stability_summary_json),
            "campaign_status": stability_status,
            "summary": stability_summary,
        },
        "hardening": {
            "run": run_hardening,
            "summary_json": str(hardening_summary_json),
            "hardening_status": hardening_status,
            "realism_gate_candidate": hardening_candidate,
            "realism_gate_candidate_status": hardening_candidate_status,
            "summary": hardening_summary,
        },
        "summary": {
            "stability_runs_requested": int(args.stability_runs),
            "threshold_profile_count": int(len(threshold_profiles)),
            "stability_status": stability_status,
            "hardening_status": hardening_status,
            "realism_gate_candidate_status": hardening_candidate_status,
            "stable_run_count": None
            if not isinstance(stability_summary, Mapping)
            else int(stability_summary.get("stable_run_count", 0)),
        },
    }
    output_summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("PO-SBR physical full-track gate lock completed.")
    print(f"  gate_lock_status: {gate_lock_status}")
    print(f"  blockers: {blockers}")
    print(f"  stability_status: {stability_status}")
    print(f"  hardening_status: {hardening_status}")
    print(f"  realism_gate_candidate: {realism_gate_candidate}")
    print(f"  realism_gate_candidate_status: {hardening_candidate_status}")
    print(f"  output_summary_json: {output_summary_json}")

    if bool(args.strict_ready) and gate_lock_status != "ready":
        raise RuntimeError("physical full-track gate lock is not ready")


if __name__ == "__main__":
    main()
