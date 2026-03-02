#!/usr/bin/env python3
"""Show PO-SBR readiness/migration progress and next actions on this Linux PC."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple


def _latest_json(reports_root: Path, pattern: str) -> Optional[Path]:
    candidates = sorted(reports_root.glob(pattern))
    if not candidates:
        return None
    candidates = [p for p in candidates if p.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object expected: {path}")
    return payload


def _run_git(repo_root: Path, args: List[str]) -> Tuple[bool, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return False, proc.stderr.strip()
    return True, proc.stdout.strip()


def _bool(v: Any) -> bool:
    return bool(v)


def _status_str(v: Any) -> str:
    return str(v).strip()


def _int_or_default(v: Any, default: int) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _build_stage(
    name: str,
    source_json: Optional[Path],
    ready: bool,
    details: Dict[str, Any],
    required: bool = True,
) -> Dict[str, Any]:
    status = "ready" if ready else "blocked"
    if source_json is None and _status_str(details.get("reason", "")) == "report_not_found":
        status = "missing"
    stage = {
        "name": name,
        "status": status,
        "ready": bool(ready),
        "required": bool(required),
        "source_json": str(source_json) if source_json is not None else None,
        "details": details,
    }
    return stage


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Print PO-SBR readiness/migration progress from latest local report artifacts "
            "and suggest next actions."
        )
    )
    p.add_argument(
        "--reports-root",
        default="docs/reports",
        help="Directory containing PO-SBR report JSON files (default: docs/reports)",
    )
    p.add_argument(
        "--output-json",
        default="",
        help="Optional output JSON path for this progress snapshot",
    )
    p.add_argument(
        "--strict-ready",
        action="store_true",
        help="Exit non-zero when any required stage is missing/blocked",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path.cwd().resolve()
    reports_root = Path(str(args.reports_root))
    if not reports_root.is_absolute():
        reports_root = (repo_root / reports_root).resolve()
    else:
        reports_root = reports_root.resolve()

    merged_path = _latest_json(reports_root, "po_sbr_physical_full_track_merged_checkpoint_*.json")
    closure_path = _latest_json(reports_root, "po_sbr_operator_handoff_closure_*.json")
    gate_path = _latest_json(reports_root, "po_sbr_post_change_gate_*.json")
    myproject_checkpoint_path = _latest_json(
        reports_root, "po_sbr_myproject_readiness_checkpoint_*.json"
    )
    local_ready_path = _latest_json(reports_root, "po_sbr_local_ready_regression_*_pc_self.json")
    drift_path = _latest_json(reports_root, "po_sbr_local_ready_baseline_drift_*_pc_self.json")

    stages: List[Dict[str, Any]] = []
    next_actions: List[str] = []

    if merged_path is None:
        stages.append(
            _build_stage(
                name="merged_checkpoint",
                source_json=None,
                ready=False,
                details={"reason": "report_not_found"},
            )
        )
        next_actions.append("Run: bash scripts/verify_po_sbr_physical_full_track_merged_ready.sh")
    else:
        merged = _load_json(merged_path)
        merged_ready = _bool(merged.get("ready"))
        status = merged.get("status")
        status_map = dict(status) if isinstance(status, Mapping) else {}
        stages.append(
            _build_stage(
                name="merged_checkpoint",
                source_json=merged_path,
                ready=merged_ready,
                details={
                    "ready": merged_ready,
                    "matrix_status": _status_str(status_map.get("matrix_status", "")),
                    "full_track_status": _status_str(status_map.get("full_track_status", "")),
                    "gate_lock_status": _status_str(status_map.get("gate_lock_status", "")),
                    "stability_status": _status_str(status_map.get("stability_status", "")),
                    "hardening_status": _status_str(status_map.get("hardening_status", "")),
                    "realism_gate_candidate_status": _status_str(
                        status_map.get("realism_gate_candidate_status", "")
                    ),
                    "generated_from_head_commit": _status_str(
                        merged.get("generated_from_head_commit", "")
                    ),
                },
            )
        )
        if not merged_ready:
            next_actions.append("Run: bash scripts/verify_po_sbr_physical_full_track_merged_ready.sh")

    if closure_path is None:
        stages.append(
            _build_stage(
                name="operator_handoff_closure",
                source_json=None,
                ready=False,
                details={"reason": "report_not_found"},
            )
        )
        next_actions.append("Run: bash scripts/verify_po_sbr_operator_handoff_closure.sh")
    else:
        closure = _load_json(closure_path)
        closure_ready = _status_str(closure.get("overall_status", "")) == "ready"
        merged_full_track = closure.get("merged_full_track")
        merged_map = dict(merged_full_track) if isinstance(merged_full_track, Mapping) else {}
        frontend = closure.get("frontend_timeline_import_audit")
        frontend_map = dict(frontend) if isinstance(frontend, Mapping) else {}
        stages.append(
            _build_stage(
                name="operator_handoff_closure",
                source_json=closure_path,
                ready=closure_ready,
                details={
                    "overall_status": _status_str(closure.get("overall_status", "")),
                    "frontend_validator_status": _status_str(
                        frontend_map.get("validator_status", "")
                    ),
                    "frontend_api_regression_status": _status_str(
                        frontend_map.get("api_regression_status", "")
                    ),
                    "merged_ready": _bool(merged_map.get("ready")),
                },
            )
        )
        if not closure_ready:
            next_actions.append("Run: bash scripts/verify_po_sbr_operator_handoff_closure.sh")

    if gate_path is None:
        stages.append(
            _build_stage(
                name="post_change_gate",
                source_json=None,
                ready=False,
                details={"reason": "report_not_found"},
            )
        )
        next_actions.append(
            "Run: PYTHONPATH=src .venv/bin/python scripts/run_po_sbr_post_change_gate.py "
            "--force-run --strict --base-ref HEAD~1 --head-ref HEAD "
            "--output-json docs/reports/po_sbr_post_change_gate_$(date -u +%Y_%m_%d).json"
        )
    else:
        gate = _load_json(gate_path)
        gate_ready = _status_str(gate.get("overall_status", "")) == "ready"
        stages.append(
            _build_stage(
                name="post_change_gate",
                source_json=gate_path,
                ready=gate_ready,
                details={
                    "overall_status": _status_str(gate.get("overall_status", "")),
                    "closure_required": _bool(gate.get("closure_required")),
                    "closure_status": _status_str(gate.get("closure_status", "")),
                    "forced": _bool(gate.get("forced")),
                },
            )
        )
        if not gate_ready:
            next_actions.append(
                "Run: PYTHONPATH=src .venv/bin/python scripts/run_po_sbr_post_change_gate.py "
                "--force-run --strict --base-ref HEAD~1 --head-ref HEAD "
                "--output-json docs/reports/po_sbr_post_change_gate_$(date -u +%Y_%m_%d).json"
            )

    if myproject_checkpoint_path is None:
        stages.append(
            _build_stage(
                name="myproject_readiness_checkpoint",
                source_json=None,
                ready=False,
                details={"reason": "report_not_found"},
                required=False,
            )
        )
        next_actions.append("Run (myproject): bash scripts/run_po_sbr_myproject_readiness_checkpoint.sh")
    else:
        myproject_checkpoint = _load_json(myproject_checkpoint_path)
        myproject_overall_status = _status_str(myproject_checkpoint.get("overall_status", ""))
        myproject_avx_status = _status_str(
            myproject_checkpoint.get("avx_developer_gate_status", "")
        )
        myproject_function_test_status = _status_str(
            myproject_checkpoint.get("function_test_overall_status", "")
        )
        myproject_local_ready_status = _status_str(
            myproject_checkpoint.get("local_ready_overall_status", "")
        )
        myproject_baseline_drift_verdict = _status_str(
            myproject_checkpoint.get("baseline_drift_verdict", "")
        )
        myproject_baseline_drift_difference_count = _int_or_default(
            myproject_checkpoint.get("baseline_drift_difference_count", -1),
            -1,
        )
        myproject_progress_snapshot_overall_ready = bool(
            myproject_checkpoint.get("progress_snapshot_overall_ready", False)
        )
        checkpoint_checks_raw = myproject_checkpoint.get("checkpoint_checks")
        checkpoint_checks = (
            dict(checkpoint_checks_raw)
            if isinstance(checkpoint_checks_raw, Mapping)
            else {}
        )
        checkpoint_checks_ready = all(
            bool(checkpoint_checks.get(key, False))
            for key in (
                "function_test_ready",
                "local_ready_ready",
                "baseline_drift_match",
                "avx_developer_gate_ready",
                "post_change_gate_validator_ok",
                "progress_snapshot_overall_ready",
                "progress_snapshot_validator_ok",
                "hook_selftest_validator_ok",
            )
        )
        myproject_post_change_validator_status = _status_str(
            myproject_checkpoint.get("post_change_gate_validator_status", "")
        )
        myproject_progress_validator_status = _status_str(
            myproject_checkpoint.get("progress_snapshot_validator_status", "")
        )
        myproject_hook_selftest_validator_status = _status_str(
            myproject_checkpoint.get("hook_selftest_validator_status", "")
        )
        myproject_ready = (
            myproject_overall_status == "ready"
            and myproject_avx_status == "ready"
            and myproject_function_test_status == "ready"
            and myproject_local_ready_status == "ready"
            and myproject_baseline_drift_verdict == "match"
            and myproject_baseline_drift_difference_count == 0
            and myproject_progress_snapshot_overall_ready
            and myproject_post_change_validator_status in {"", "pass", "skipped"}
            and myproject_progress_validator_status in {"", "pass", "skipped"}
            and myproject_hook_selftest_validator_status in {"", "pass", "skipped"}
            and checkpoint_checks_ready
        )
        stages.append(
            _build_stage(
                name="myproject_readiness_checkpoint",
                source_json=myproject_checkpoint_path,
                ready=myproject_ready,
                required=False,
                details={
                    "overall_status": myproject_overall_status,
                    "avx_developer_gate_status": myproject_avx_status,
                    "function_test_overall_status": myproject_function_test_status,
                    "local_ready_overall_status": myproject_local_ready_status,
                    "baseline_drift_verdict": myproject_baseline_drift_verdict,
                    "baseline_drift_difference_count": myproject_baseline_drift_difference_count,
                    "progress_snapshot_overall_ready": myproject_progress_snapshot_overall_ready,
                    "post_change_gate_validator_status": myproject_post_change_validator_status,
                    "progress_snapshot_validator_status": myproject_progress_validator_status,
                    "hook_selftest_validator_status": myproject_hook_selftest_validator_status,
                    "checkpoint_checks_ready": checkpoint_checks_ready,
                },
            )
        )
        if not myproject_ready:
            next_actions.append("Run (myproject): bash scripts/run_po_sbr_myproject_readiness_checkpoint.sh")

    if local_ready_path is None:
        stages.append(
            _build_stage(
                name="myproject_local_ready",
                source_json=None,
                ready=False,
                details={"reason": "report_not_found"},
            )
        )
        next_actions.append(
            "Run (myproject): PYTHONPATH=src .venv-po-sbr/bin/python "
            "scripts/run_po_sbr_local_ready_regression.py --strict-ready"
        )
    else:
        local_ready = _load_json(local_ready_path)
        summary = local_ready.get("summary")
        summary_map = dict(summary) if isinstance(summary, Mapping) else {}
        local_ready_ok = _status_str(summary_map.get("overall_status", "")) == "ready"
        stages.append(
            _build_stage(
                name="myproject_local_ready",
                source_json=local_ready_path,
                ready=local_ready_ok,
                details={
                    "overall_status": _status_str(summary_map.get("overall_status", "")),
                    "golden_path_status": _status_str(summary_map.get("golden_path_status", "")),
                    "kpi_campaign_status": _status_str(summary_map.get("kpi_campaign_status", "")),
                    "kpi_scenario_matrix_status": _status_str(
                        summary_map.get("kpi_scenario_matrix_status", "")
                    ),
                    "gate_lock_status": _status_str(summary_map.get("gate_lock_status", "")),
                },
            )
        )
        if not local_ready_ok:
            next_actions.append(
                "Run (myproject): PYTHONPATH=src .venv-po-sbr/bin/python "
                "scripts/run_po_sbr_local_ready_regression.py --strict-ready"
            )

    if drift_path is None:
        stages.append(
            _build_stage(
                name="myproject_baseline_drift",
                source_json=None,
                ready=False,
                details={"reason": "report_not_found"},
            )
        )
        next_actions.append(
            "Run (myproject): PYTHONPATH=src .venv-po-sbr/bin/python "
            "scripts/check_po_sbr_local_ready_baseline_drift.py --require-match --require-candidate-ready"
        )
    else:
        drift = _load_json(drift_path)
        drift_ok = (
            _status_str(drift.get("drift_verdict", "")) == "match"
            and int(drift.get("difference_count", -1)) == 0
        )
        stages.append(
            _build_stage(
                name="myproject_baseline_drift",
                source_json=drift_path,
                ready=drift_ok,
                details={
                    "drift_verdict": _status_str(drift.get("drift_verdict", "")),
                    "difference_count": int(drift.get("difference_count", 0)),
                },
            )
        )
        if not drift_ok:
            next_actions.append(
                "Run (myproject): PYTHONPATH=src .venv-po-sbr/bin/python "
                "scripts/check_po_sbr_local_ready_baseline_drift.py --require-match --require-candidate-ready"
            )

    hook_ok, hook_value = _run_git(repo_root, ["config", "--get", "core.hooksPath"])
    hook_path = hook_value if hook_ok else ""
    hook_ready = hook_ok and hook_path == ".githooks"
    stages.append(
        _build_stage(
            name="local_pre_push_hook",
            source_json=None,
            ready=hook_ready,
            details={
                "core_hooks_path": hook_path,
                "installed": hook_ready,
            },
        )
    )
    if not hook_ready:
        next_actions.append("Run: ./scripts/install_po_sbr_pre_push_hook.sh")

    required_stages = [stage for stage in stages if bool(stage.get("required", True))]
    optional_stages = [stage for stage in stages if not bool(stage.get("required", True))]

    total = len(required_stages)
    ready_count = sum(1 for stage in required_stages if stage["status"] == "ready")
    missing_count = sum(1 for stage in required_stages if stage["status"] == "missing")
    blocked_count = total - ready_count - missing_count
    progress_ratio = (float(ready_count) / float(total)) if total > 0 else 0.0
    overall_ready = ready_count == total

    dedup_next_actions: List[str] = []
    seen_actions = set()
    for action in next_actions:
        if action in seen_actions:
            continue
        dedup_next_actions.append(action)
        seen_actions.add(action)

    if overall_ready:
        dedup_next_actions = [
            "All readiness checks are green. Continue feature development; pre-push gate will enforce closure policy."
        ]

    payload = {
        "report_name": "po_sbr_progress_snapshot",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(repo_root),
        "reports_root": str(reports_root),
        "overall_ready": overall_ready,
        "progress": {
            "ready_count": ready_count,
            "blocked_count": blocked_count,
            "missing_count": missing_count,
            "total_count": total,
            "progress_ratio": progress_ratio,
            "optional_total_count": len(optional_stages),
            "optional_ready_count": sum(
                1 for stage in optional_stages if stage.get("status") == "ready"
            ),
            "optional_missing_count": sum(
                1 for stage in optional_stages if stage.get("status") == "missing"
            ),
        },
        "stages": stages,
        "next_actions": dedup_next_actions,
    }

    print("PO-SBR progress snapshot")
    print(f"workspace_root={repo_root}")
    print(f"overall_ready={overall_ready}")
    print(
        "progress="
        f"{ready_count}/{total} ready "
        f"({progress_ratio * 100.0:.1f}%), blocked={blocked_count}, missing={missing_count}"
    )
    for stage in stages:
        source = stage.get("source_json")
        source_text = str(source) if source else "-"
        required = bool(stage.get("required", True))
        print(
            f"- {stage['name']}: {stage['status']} "
            f"(required={required}, source={source_text})"
        )
    print("next_actions:")
    for action in dedup_next_actions:
        print(f"- {action}")

    output_json = str(args.output_json).strip()
    if output_json:
        output_path = Path(output_json).expanduser()
        if not output_path.is_absolute():
            output_path = (repo_root / output_path).resolve()
        else:
            output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"wrote {output_path}")

    if bool(args.strict_ready) and not overall_ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
