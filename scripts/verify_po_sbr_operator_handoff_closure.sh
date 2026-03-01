#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PY_DET="${ROOT_DIR}/.venv/bin/python"
VERIFY_MERGED_SCRIPT="${ROOT_DIR}/scripts/verify_po_sbr_physical_full_track_merged_ready.sh"
CHECKPOINT_JSON_DEFAULT="${ROOT_DIR}/docs/reports/po_sbr_physical_full_track_merged_checkpoint_2026_03_01.json"
CHECKPOINT_JSON="${PO_SBR_MERGED_CHECKPOINT_JSON_OVERRIDE:-${CHECKPOINT_JSON_DEFAULT}}"
STAMP="$(date +%Y_%m_%d)"
OUT_JSON_DEFAULT="${ROOT_DIR}/docs/reports/po_sbr_operator_handoff_closure_${STAMP}.json"
OUT_JSON="${1:-${PO_SBR_CLOSURE_JSON_OVERRIDE:-${OUT_JSON_DEFAULT}}}"

require_file() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    echo "missing required file: ${path}" >&2
    exit 1
  fi
}

if [[ ! -x "${PY_DET}" ]]; then
  echo "missing python interpreter: ${PY_DET}" >&2
  exit 1
fi
require_file "${VERIFY_MERGED_SCRIPT}"

echo "[closure] frontend timeline-import-audit sweep (M17.97~M17.101)"
PYTHONPATH=src "${PY_DET}" scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_apply_refresh.py
PYTHONPATH=src "${PY_DET}" scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_safety_refresh.py
PYTHONPATH=src "${PY_DET}" scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_trail_refresh.py
PYTHONPATH=src "${PY_DET}" scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_controls_refresh.py
PYTHONPATH=src "${PY_DET}" scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_apply_trail_refresh.py
PYTHONPATH=src "${PY_DET}" scripts/validate_web_e2e_orchestrator_api.py

echo "[closure] merged full-track readiness verifier"
bash "${VERIFY_MERGED_SCRIPT}"
require_file "${CHECKPOINT_JSON}"

echo "[closure] write operator handoff snapshot: ${OUT_JSON}"
PYTHONPATH=src "${PY_DET}" - "${ROOT_DIR}" "${CHECKPOINT_JSON}" "${OUT_JSON}" <<'PY'
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    checkpoint_json = Path(sys.argv[2]).resolve()
    out_json = Path(sys.argv[3]).resolve()

    checkpoint = json.loads(checkpoint_json.read_text(encoding="utf-8"))
    status = checkpoint.get("status") or {}

    payload = {
        "report_name": "po_sbr_operator_handoff_closure",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(root),
        "branch": _git(root, "branch", "--show-current"),
        "head_commit": _git(root, "rev-parse", "HEAD"),
        "frontend_timeline_import_audit": {
            "milestones": ["M17.97", "M17.98", "M17.99", "M17.100", "M17.101"],
            "validator_status": "pass",
            "api_regression_status": "pass",
        },
        "merged_full_track": {
            "checkpoint_json": str(checkpoint_json),
            "ready": bool(checkpoint.get("ready", False)),
            "matrix_status": status.get("matrix_status"),
            "full_track_status": status.get("full_track_status"),
            "gate_lock_status": status.get("gate_lock_status"),
            "realism_gate_candidate_status": status.get("realism_gate_candidate_status"),
            "generated_from_head_commit": checkpoint.get("generated_from_head_commit"),
            "merged_readiness_commit": checkpoint.get("merged_readiness_commit"),
        },
    }
    payload["overall_status"] = (
        "ready"
        if (
            payload["frontend_timeline_import_audit"]["validator_status"] == "pass"
            and payload["frontend_timeline_import_audit"]["api_regression_status"] == "pass"
            and payload["merged_full_track"]["ready"]
        )
        else "blocked"
    )

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out_json}")
    print(f"overall_status={payload['overall_status']}")


if __name__ == "__main__":
    main()
PY

echo "[closure] PASS: operator handoff closure is healthy"
