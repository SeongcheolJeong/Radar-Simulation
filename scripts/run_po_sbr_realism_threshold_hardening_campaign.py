#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


THRESHOLD_PROFILES: Dict[str, Dict[str, float]] = {
    "realism_tight_v1": {
        "rd_shape_nmse_max": 0.10,
        "ra_shape_nmse_max": 0.10,
        "rd_peak_power_db_abs_error_max": 1.00,
        "ra_peak_power_db_abs_error_max": 1.00,
        "rd_centroid_range_bin_abs_error_max": 1.00,
        "ra_centroid_angle_bin_abs_error_max": 1.00,
        "rd_spread_range_rel_error_max": 0.20,
        "ra_spread_angle_rel_error_max": 0.20,
    },
    "realism_tight_v2": {
        "rd_shape_nmse_max": 0.02,
        "ra_shape_nmse_max": 0.02,
        "rd_peak_power_db_abs_error_max": 0.10,
        "ra_peak_power_db_abs_error_max": 0.10,
        "rd_centroid_range_bin_abs_error_max": 0.50,
        "ra_centroid_angle_bin_abs_error_max": 0.50,
        "rd_spread_range_rel_error_max": 0.10,
        "ra_spread_angle_rel_error_max": 0.10,
    },
    "realism_tight_v3": {
        "rd_shape_nmse_max": 0.005,
        "ra_shape_nmse_max": 0.005,
        "rd_peak_power_db_abs_error_max": 0.02,
        "ra_peak_power_db_abs_error_max": 0.02,
        "rd_centroid_range_bin_abs_error_max": 0.10,
        "ra_centroid_angle_bin_abs_error_max": 0.10,
        "rd_spread_range_rel_error_max": 0.05,
        "ra_spread_angle_rel_error_max": 0.05,
    },
}
DEFAULT_THRESHOLD_PROFILES = tuple(THRESHOLD_PROFILES.keys())
DEFAULT_REALISM_GATE_CANDIDATE = "realism_tight_v2"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Run realism-profile KPI threshold hardening campaign on top of a ready physical "
            "full-track bundle and emit one hardening report."
        )
    )
    p.add_argument(
        "--full-track-bundle-summary-json",
        required=True,
        help="Input summary JSON from scripts/run_po_sbr_physical_full_track_bundle.py",
    )
    p.add_argument(
        "--stability-summary-json",
        default=None,
        help="Optional stability summary JSON (campaign_status should be stable)",
    )
    p.add_argument("--output-root", required=True, help="Output root directory")
    p.add_argument("--output-summary-json", required=True, help="Output hardening summary JSON path")
    p.add_argument(
        "--threshold-profile",
        action="append",
        default=[],
        help=(
            "Threshold profile id to evaluate (repeatable, comma-separated allowed). "
            "Default: realism_tight_v1, realism_tight_v2, realism_tight_v3"
        ),
    )
    p.add_argument(
        "--realism-gate-candidate",
        default=DEFAULT_REALISM_GATE_CANDIDATE,
        help=f"Realism threshold profile promoted as gate candidate (default: {DEFAULT_REALISM_GATE_CANDIDATE})",
    )
    p.add_argument(
        "--strict-hardened",
        action="store_true",
        help="Exit non-zero unless hardening_status=hardened",
    )
    p.add_argument(
        "--python-bin",
        default=str(sys.executable),
        help="Python interpreter used for subprocess runner calls",
    )
    return p.parse_args()


def _parse_threshold_profiles(items: Sequence[str]) -> List[str]:
    if len(items) == 0:
        return list(DEFAULT_THRESHOLD_PROFILES)
    out: List[str] = []
    for raw in items:
        for token in str(raw).split(","):
            profile = str(token).strip()
            if profile == "":
                continue
            if profile not in THRESHOLD_PROFILES:
                raise ValueError(f"unsupported threshold profile: {profile}")
            if profile not in out:
                out.append(profile)
    if len(out) == 0:
        raise ValueError("at least one threshold profile must be selected")
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


def _write_threshold_json(path: Path, payload: Mapping[str, float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({str(k): float(v) for k, v in payload.items()}, indent=2), encoding="utf-8")


def _profile_row_result(
    profile_name: str,
    source_row: Mapping[str, Any],
    thresholds_json: Path,
    output_json: Path,
    run_kpi: Mapping[str, Any],
    validate_kpi: Mapping[str, Any],
) -> Dict[str, Any]:
    row = {
        "profile": profile_name,
        "profile_family": str(source_row.get("profile_family", "")).strip() or None,
        "source_golden_summary_json": str(source_row.get("golden_summary_json", "")).strip() or None,
        "thresholds_json": str(thresholds_json),
        "output_kpi_json": str(output_json),
        "run_kpi": dict(run_kpi),
        "validate_kpi": dict(validate_kpi),
        "run_ok": False,
        "campaign_status": None,
        "blockers": [],
        "parity_fail_count": None,
        "parity_fail_pairs": [],
    }
    if not bool(run_kpi.get("ok", False)):
        return row
    if not bool(validate_kpi.get("ok", False)):
        return row
    if not output_json.exists():
        return row
    payload = _load_json(output_json)
    row["run_ok"] = True
    row["campaign_status"] = str(payload.get("campaign_status", "")).strip() or None
    row["blockers"] = list(payload.get("blockers", []) if isinstance(payload.get("blockers"), list) else [])
    summary = payload.get("summary")
    if isinstance(summary, Mapping):
        row["parity_fail_count"] = int(summary.get("parity_fail_count", 0))
        row["parity_fail_pairs"] = list(
            summary.get("parity_fail_pairs", []) if isinstance(summary.get("parity_fail_pairs"), list) else []
        )
    return row


def main() -> None:
    args = parse_args()
    threshold_profiles = _parse_threshold_profiles(args.threshold_profile)
    realism_gate_candidate = str(args.realism_gate_candidate).strip()
    if realism_gate_candidate == "":
        raise ValueError("--realism-gate-candidate must be non-empty")
    if realism_gate_candidate not in THRESHOLD_PROFILES:
        raise ValueError(f"unsupported --realism-gate-candidate: {realism_gate_candidate}")
    if realism_gate_candidate not in threshold_profiles:
        threshold_profiles.append(realism_gate_candidate)

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

    full_track_summary_json = Path(args.full_track_bundle_summary_json).expanduser()
    if not full_track_summary_json.is_absolute():
        full_track_summary_json = (cwd / full_track_summary_json).resolve()
    else:
        full_track_summary_json = full_track_summary_json.resolve()
    if not full_track_summary_json.exists():
        raise FileNotFoundError(f"full-track bundle summary not found: {full_track_summary_json}")
    full_track_payload = _load_json(full_track_summary_json)

    stability_payload: Optional[Dict[str, Any]] = None
    stability_summary_json: Optional[Path] = None
    if args.stability_summary_json is not None:
        stability_summary_json = Path(args.stability_summary_json).expanduser()
        if not stability_summary_json.is_absolute():
            stability_summary_json = (cwd / stability_summary_json).resolve()
        else:
            stability_summary_json = stability_summary_json.resolve()
        if not stability_summary_json.exists():
            raise FileNotFoundError(f"stability summary not found: {stability_summary_json}")
        stability_payload = _load_json(stability_summary_json)

    python_path = Path(str(args.python_bin)).expanduser()
    if not python_path.is_absolute():
        python_path = (cwd / python_path).resolve()
    python_bin = str(python_path)

    rows_raw = full_track_payload.get("rows")
    if not isinstance(rows_raw, list):
        raise ValueError("full-track bundle summary missing rows list")

    realism_rows: List[Dict[str, Any]] = []
    for item in rows_raw:
        if not isinstance(item, Mapping):
            continue
        family = str(item.get("profile_family", "")).strip()
        if family != "realism_informational":
            continue
        profile = str(item.get("profile", "")).strip()
        golden_summary_json = str(item.get("golden_summary_json", "")).strip()
        if profile == "" or golden_summary_json == "":
            continue
        realism_rows.append(dict(item))

    by_threshold: List[Dict[str, Any]] = []
    for threshold_profile in threshold_profiles:
        threshold_root = output_root / threshold_profile
        threshold_root.mkdir(parents=True, exist_ok=True)
        thresholds_json = threshold_root / "thresholds.json"
        _write_threshold_json(thresholds_json, THRESHOLD_PROFILES[threshold_profile])

        profile_rows: List[Dict[str, Any]] = []
        for source_row in realism_rows:
            profile = str(source_row["profile"])
            golden_summary_json = Path(str(source_row["golden_summary_json"])).resolve()
            profile_root = threshold_root / profile
            profile_root.mkdir(parents=True, exist_ok=True)
            kpi_output_json = profile_root / "kpi_hardened.json"

            run_kpi = _run_cmd(
                [
                    python_bin,
                    "scripts/run_scene_backend_kpi_campaign.py",
                    "--golden-path-summary-json",
                    str(golden_summary_json),
                    "--thresholds-json",
                    str(thresholds_json),
                    "--output-summary-json",
                    str(kpi_output_json),
                ],
                cwd=cwd,
            )
            validate_kpi = _run_cmd(
                [
                    python_bin,
                    "scripts/validate_scene_backend_kpi_campaign_report.py",
                    "--summary-json",
                    str(kpi_output_json),
                ],
                cwd=cwd,
            )
            profile_rows.append(
                _profile_row_result(
                    profile_name=profile,
                    source_row=source_row,
                    thresholds_json=thresholds_json,
                    output_json=kpi_output_json,
                    run_kpi=run_kpi,
                    validate_kpi=validate_kpi,
                )
            )

        run_error_count = int(sum(1 for row in profile_rows if not bool(row.get("run_ok", False))))
        ready_count = int(sum(1 for row in profile_rows if str(row.get("campaign_status", "")) == "ready"))
        blocked_count = int(sum(1 for row in profile_rows if str(row.get("campaign_status", "")) == "blocked"))
        total_parity_fail_count = int(
            sum(int(row.get("parity_fail_count") or 0) for row in profile_rows if bool(row.get("run_ok", False)))
        )
        status = "ready"
        if run_error_count > 0:
            status = "failed"
        elif blocked_count > 0:
            status = "blocked"

        by_threshold.append(
            {
                "threshold_profile": threshold_profile,
                "thresholds_json": str(thresholds_json),
                "thresholds": THRESHOLD_PROFILES[threshold_profile],
                "status": status,
                "summary": {
                    "profile_count": int(len(profile_rows)),
                    "ready_profile_count": ready_count,
                    "blocked_profile_count": blocked_count,
                    "failed_profile_count": run_error_count,
                    "total_parity_fail_count": total_parity_fail_count,
                },
                "rows": profile_rows,
            }
        )

    bundle_status = str(full_track_payload.get("full_track_status", "")).strip()
    bundle_summary = full_track_payload.get("summary")
    bundle_gate_blocked = None
    if isinstance(bundle_summary, Mapping):
        bundle_gate_blocked = int(bundle_summary.get("gate_blocked_profile_count", 0))
    stability_status = None if stability_payload is None else str(stability_payload.get("campaign_status", "")).strip()

    threshold_failed_count = int(
        sum(1 for row in by_threshold if str(row.get("status", "")) not in ("ready",))
    )
    candidate_row = next(
        (row for row in by_threshold if str(row.get("threshold_profile", "")) == realism_gate_candidate),
        None,
    )
    candidate_status = None if candidate_row is None else str(candidate_row.get("status", "")).strip()
    blockers: List[str] = []
    if bundle_status != "ready":
        blockers.append("full_track_bundle_not_ready")
    if (bundle_gate_blocked is not None) and bundle_gate_blocked > 0:
        blockers.append("full_track_gate_blocked")
    if stability_payload is not None and stability_status != "stable":
        blockers.append("stability_campaign_not_stable")
    if len(realism_rows) == 0:
        blockers.append("no_realism_profiles_found")
    if threshold_failed_count > 0:
        blockers.append("threshold_profile_not_ready")
    if candidate_row is None:
        blockers.append("realism_gate_candidate_not_evaluated")
    elif candidate_status != "ready":
        blockers.append("realism_gate_candidate_not_ready")

    hardening_status = "hardened" if len(blockers) == 0 else "blocked"
    report = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "workspace_root": str(cwd),
        "python_executable": str(Path(sys.executable).resolve()),
        "hardening_status": hardening_status,
        "blockers": blockers,
        "source_full_track_bundle_summary_json": str(full_track_summary_json),
        "source_stability_summary_json": str(stability_summary_json) if stability_summary_json is not None else None,
        "source_full_track_status": bundle_status,
        "source_stability_status": stability_status,
        "realism_gate_candidate": realism_gate_candidate,
        "realism_gate_candidate_status": candidate_status,
        "threshold_profiles": threshold_profiles,
        "realism_profile_names": [str(item.get("profile")) for item in realism_rows],
        "profiles": by_threshold,
        "summary": {
            "threshold_profile_count": int(len(by_threshold)),
            "threshold_ready_count": int(
                sum(1 for row in by_threshold if str(row.get("status", "")) == "ready")
            ),
            "threshold_failed_count": threshold_failed_count,
            "realism_profile_count": int(len(realism_rows)),
            "bundle_gate_blocked_profile_count": bundle_gate_blocked,
            "realism_gate_candidate_status": candidate_status,
        },
    }
    output_summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("PO-SBR realism threshold hardening campaign completed.")
    print(f"  hardening_status: {hardening_status}")
    print(f"  blockers: {blockers}")
    print(f"  realism_gate_candidate: {realism_gate_candidate}")
    print(f"  realism_gate_candidate_status: {candidate_status}")
    print(f"  threshold_profile_count: {len(by_threshold)}")
    print(f"  realism_profile_count: {len(realism_rows)}")
    print(f"  output_summary_json: {output_summary_json}")

    if bool(args.strict_hardened) and hardening_status != "hardened":
        raise RuntimeError("realism threshold hardening campaign is not hardened")


if __name__ == "__main__":
    main()
