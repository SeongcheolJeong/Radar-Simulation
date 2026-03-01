#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Compare a candidate local-ready regression report against a frozen "
            "PO-SBR baseline manifest and detect readiness drift."
        )
    )
    p.add_argument(
        "--baseline-manifest-json",
        required=True,
        help="Input manifest from scripts/freeze_po_sbr_local_ready_baseline.py",
    )
    p.add_argument(
        "--candidate-summary-json",
        required=True,
        help="Candidate summary from scripts/run_po_sbr_local_ready_regression.py",
    )
    p.add_argument(
        "--output-json",
        required=True,
        help="Output drift comparison report JSON path",
    )
    p.add_argument(
        "--require-match",
        action="store_true",
        help="Exit non-zero when drift_verdict != match",
    )
    p.add_argument(
        "--require-candidate-ready",
        action="store_true",
        help="Exit non-zero when candidate summary.overall_status != ready",
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


def _get_dotted(payload: Mapping[str, Any], dotted: str) -> Any:
    cur: Any = payload
    for token in dotted.split("."):
        if not isinstance(cur, Mapping):
            return None
        cur = cur.get(token)
    return cur


def _coerce_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return json.dumps(value, sort_keys=True)


def _compare_fields(
    baseline: Mapping[str, Any],
    candidate: Mapping[str, Any],
    dotted_fields: List[str],
) -> List[Dict[str, Any]]:
    diffs: List[Dict[str, Any]] = []
    for field in dotted_fields:
        base_value = _coerce_scalar(_get_dotted(baseline, field))
        cand_value = _coerce_scalar(_get_dotted(candidate, field))
        if base_value != cand_value:
            diffs.append(
                {
                    "field": field,
                    "baseline": base_value,
                    "candidate": cand_value,
                }
            )
    return diffs


def _baseline_regression_summary_path(manifest: Mapping[str, Any]) -> Path:
    frozen_files = _mapping(manifest.get("frozen_files"))
    local_ready = _mapping(frozen_files.get("po_sbr_local_ready_regression"))
    text = str(local_ready.get("frozen_path", "")).strip()
    if text == "":
        raise ValueError("manifest.frozen_files.po_sbr_local_ready_regression.frozen_path missing")
    path = Path(text).expanduser()
    if not path.is_absolute():
        raise ValueError("baseline frozen local-ready summary path must be absolute")
    if not path.exists():
        raise FileNotFoundError(f"baseline frozen local-ready summary not found: {path}")
    return path.resolve()


def _status_snapshot(payload: Mapping[str, Any]) -> Dict[str, Any]:
    reports = _mapping(payload.get("reports"))
    return {
        "overall_status": _get_dotted(payload, "summary.overall_status"),
        "golden_path_status": _get_dotted(payload, "summary.golden_path_status"),
        "kpi_campaign_status": _get_dotted(payload, "summary.kpi_campaign_status"),
        "kpi_scenario_matrix_status": _get_dotted(payload, "summary.kpi_scenario_matrix_status"),
        "gate_lock_status": _get_dotted(payload, "summary.gate_lock_status"),
        "golden_migration_status": _get_dotted(reports, "golden_path.migration_status"),
        "kpi_parity_fail_count": _get_dotted(reports, "kpi_campaign.parity_fail_count"),
        "matrix_blocked_profile_count": _get_dotted(reports, "kpi_scenario_matrix.blocked_profile_count"),
        "matrix_failed_profile_count": _get_dotted(reports, "kpi_scenario_matrix.failed_profile_count"),
        "gate_lock_stability_status": _get_dotted(reports, "gate_lock.stability_status"),
        "gate_lock_hardening_status": _get_dotted(reports, "gate_lock.hardening_status"),
        "gate_lock_realism_gate_candidate_status": _get_dotted(
            reports, "gate_lock.realism_gate_candidate_status"
        ),
    }


def main() -> None:
    args = parse_args()
    cwd = Path.cwd().resolve()

    manifest_json = _resolve_path(args.baseline_manifest_json, cwd=cwd)
    candidate_summary_json = _resolve_path(args.candidate_summary_json, cwd=cwd)
    output_json = _resolve_path(args.output_json, cwd=cwd)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    if not manifest_json.exists():
        raise FileNotFoundError(f"baseline manifest not found: {manifest_json}")
    if not candidate_summary_json.exists():
        raise FileNotFoundError(f"candidate summary not found: {candidate_summary_json}")

    manifest = _load_json(manifest_json)
    baseline_summary_json = _baseline_regression_summary_path(manifest=manifest)
    baseline_summary = _load_json(baseline_summary_json)
    candidate_summary = _load_json(candidate_summary_json)

    compare_fields = [
        "summary.overall_status",
        "summary.golden_path_status",
        "summary.kpi_campaign_status",
        "summary.kpi_scenario_matrix_status",
        "summary.gate_lock_status",
        "reports.golden_path.status",
        "reports.golden_path.migration_status",
        "reports.golden_path.executed_count",
        "reports.golden_path.requested_count",
        "reports.kpi_campaign.status",
        "reports.kpi_campaign.campaign_status",
        "reports.kpi_campaign.parity_fail_count",
        "reports.kpi_scenario_matrix.status",
        "reports.kpi_scenario_matrix.matrix_status",
        "reports.kpi_scenario_matrix.profile_count",
        "reports.kpi_scenario_matrix.blocked_profile_count",
        "reports.kpi_scenario_matrix.failed_profile_count",
        "reports.gate_lock.status",
        "reports.gate_lock.gate_lock_status",
        "reports.gate_lock.stability_status",
        "reports.gate_lock.hardening_status",
        "reports.gate_lock.realism_gate_candidate_status",
    ]
    differences = _compare_fields(
        baseline=baseline_summary,
        candidate=candidate_summary,
        dotted_fields=compare_fields,
    )

    blockers: List[str] = []
    candidate_overall_status = str(_get_dotted(candidate_summary, "summary.overall_status") or "").strip()
    if bool(args.require_candidate_ready) and candidate_overall_status != "ready":
        blockers.append("candidate_overall_status_not_ready")

    drift_verdict = "match" if len(differences) == 0 else "mismatch"
    if drift_verdict != "match":
        blockers.append("readiness_field_drift_detected")

    report = {
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_manifest_json": str(manifest_json),
        "baseline_summary_json": str(baseline_summary_json),
        "candidate_summary_json": str(candidate_summary_json),
        "drift_verdict": drift_verdict,
        "difference_count": len(differences),
        "differences": differences,
        "blockers": blockers,
        "baseline_status_snapshot": _status_snapshot(baseline_summary),
        "candidate_status_snapshot": _status_snapshot(candidate_summary),
    }
    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("PO-SBR local-ready baseline drift check completed.")
    print(f"  drift_verdict: {drift_verdict}")
    print(f"  difference_count: {len(differences)}")
    print(f"  blockers: {blockers}")
    print(f"  output_json: {output_json}")

    if bool(args.require_match) and drift_verdict != "match":
        raise RuntimeError("baseline drift mismatch detected")
    if bool(args.require_candidate_ready) and candidate_overall_status != "ready":
        raise RuntimeError(f"candidate overall_status is not ready: {candidate_overall_status}")


if __name__ == "__main__":
    main()
