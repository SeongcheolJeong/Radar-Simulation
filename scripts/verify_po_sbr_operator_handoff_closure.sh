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
AVX_GATE_JSON_DEFAULT="${ROOT_DIR}/docs/reports/po_sbr_avx_developer_gate_${STAMP}.json"
AVX_GATE_JSON="${PO_SBR_AVX_DEVELOPER_GATE_SUMMARY_JSON_OVERRIDE:-${AVX_GATE_JSON_DEFAULT}}"
AVX_GATE_MATRIX_JSON_DEFAULT="${ROOT_DIR}/docs/reports/avx_export_benchmark_matrix_${STAMP}_developer_gate/summary.json"
AVX_GATE_MATRIX_JSON="${PO_SBR_AVX_DEVELOPER_GATE_MATRIX_SUMMARY_JSON_OVERRIDE:-${AVX_GATE_MATRIX_JSON_DEFAULT}}"
AVX_GATE_MATRIX_ROOT="${PO_SBR_AVX_DEVELOPER_GATE_MATRIX_ROOT_OVERRIDE:-}"
AVX_GATE_MIN_PHYSICS_BETTER_COUNT="${PO_SBR_AVX_DEVELOPER_GATE_MIN_PHYSICS_BETTER_COUNT:-1}"
AVX_GATE_ALLOW_FUNCTION_NONBETTER="${PO_SBR_AVX_DEVELOPER_GATE_ALLOW_FUNCTION_NONBETTER:-0}"
AVX_GATE_DISABLE_AUTO_TUNE="${PO_SBR_AVX_DEVELOPER_GATE_DISABLE_AUTO_TUNE:-0}"
EM_POLICY_JSON_DEFAULT="${ROOT_DIR}/docs/em_solver_packaging_policy.json"
EM_POLICY_JSON="${PO_SBR_EM_POLICY_JSON_OVERRIDE:-${EM_POLICY_JSON_DEFAULT}}"
EM_REFERENCE_LOCKS_MD_DEFAULT="${ROOT_DIR}/external/reference-locks.md"
EM_REFERENCE_LOCKS_MD="${PO_SBR_EM_REFERENCE_LOCKS_MD_OVERRIDE:-${EM_REFERENCE_LOCKS_MD_DEFAULT}}"

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
require_file "${EM_POLICY_JSON}"
require_file "${EM_REFERENCE_LOCKS_MD}"

echo "[closure] frontend timeline-import-audit sweep (M17.97~M17.101)"
PYTHONPATH=src "${PY_DET}" scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_apply_refresh.py
PYTHONPATH=src "${PY_DET}" scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_safety_refresh.py
PYTHONPATH=src "${PY_DET}" scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_trail_refresh.py
PYTHONPATH=src "${PY_DET}" scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_controls_refresh.py
PYTHONPATH=src "${PY_DET}" scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_apply_trail_refresh.py
API_REGRESSION_STATUS="pass"
if [[ "${PO_SBR_SKIP_WEB_E2E_VALIDATOR:-0}" == "1" ]]; then
  echo "[closure] skip web e2e api validator (PO_SBR_SKIP_WEB_E2E_VALIDATOR=1)"
  API_REGRESSION_STATUS="skipped"
else
  PYTHONPATH=src "${PY_DET}" scripts/validate_web_e2e_orchestrator_api.py
fi

echo "[closure] merged full-track readiness verifier"
MERGED_FULL_TRACK_VALIDATION_STATUS="pass"
if [[ "${PO_SBR_SKIP_MERGED_FULL_TRACK_VERIFIER:-0}" == "1" ]]; then
  echo "[closure] skip merged full-track verifier (PO_SBR_SKIP_MERGED_FULL_TRACK_VERIFIER=1)"
  MERGED_FULL_TRACK_VALIDATION_STATUS="skipped"
else
  bash "${VERIFY_MERGED_SCRIPT}"
fi
require_file "${CHECKPOINT_JSON}"

echo "[closure] AVX developer strict gate"
AVX_GATE_RUN_CMD=(
  scripts/run_po_sbr_avx_developer_gate.py
  --matrix-summary-json "${AVX_GATE_MATRIX_JSON}"
  --output-summary-json "${AVX_GATE_JSON}"
  --min-physics-better-count "${AVX_GATE_MIN_PHYSICS_BETTER_COUNT}"
  --strict-ready
)
if [[ -n "${AVX_GATE_MATRIX_ROOT}" ]]; then
  AVX_GATE_RUN_CMD+=(--matrix-root "${AVX_GATE_MATRIX_ROOT}")
fi
if [[ "${AVX_GATE_ALLOW_FUNCTION_NONBETTER}" == "1" ]]; then
  AVX_GATE_RUN_CMD+=(--allow-function-nonbetter)
fi
if [[ "${AVX_GATE_DISABLE_AUTO_TUNE}" == "1" ]]; then
  AVX_GATE_RUN_CMD+=(--disable-auto-tune)
fi
PYTHONPATH=src "${PY_DET}" "${AVX_GATE_RUN_CMD[@]}"
AVX_GATE_VALIDATE_CMD=(
  scripts/validate_po_sbr_avx_developer_gate_report.py
  --summary-json "${AVX_GATE_JSON}"
  --require-ready
  --min-physics-better-count "${AVX_GATE_MIN_PHYSICS_BETTER_COUNT}"
)
if [[ "${AVX_GATE_ALLOW_FUNCTION_NONBETTER}" != "1" ]]; then
  AVX_GATE_VALIDATE_CMD+=(--require-function-better-all)
fi
PYTHONPATH=src "${PY_DET}" "${AVX_GATE_VALIDATE_CMD[@]}"
require_file "${AVX_GATE_JSON}"
require_file "${AVX_GATE_MATRIX_JSON}"

EM_POLICY_VALIDATOR_STATUS="skipped"
if [[ "${PO_SBR_SKIP_EM_POLICY_VALIDATOR:-0}" != "1" ]]; then
  echo "[closure] validate EM solver packaging policy"
  PYTHONPATH=src "${PY_DET}" scripts/validate_em_solver_packaging_policy.py \
    --policy-json "${EM_POLICY_JSON}" \
    --reference-locks-md "${EM_REFERENCE_LOCKS_MD}"
  EM_POLICY_VALIDATOR_STATUS="pass"
else
  echo "[closure] skip EM solver packaging policy validator (PO_SBR_SKIP_EM_POLICY_VALIDATOR=1)"
fi

echo "[closure] write operator handoff snapshot: ${OUT_JSON}"
PYTHONPATH=src "${PY_DET}" - "${ROOT_DIR}" "${CHECKPOINT_JSON}" "${AVX_GATE_JSON}" "${AVX_GATE_MATRIX_JSON}" "${OUT_JSON}" "${API_REGRESSION_STATUS}" "${MERGED_FULL_TRACK_VALIDATION_STATUS}" "${EM_POLICY_JSON}" "${EM_REFERENCE_LOCKS_MD}" "${EM_POLICY_VALIDATOR_STATUS}" <<'PY'
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
    avx_gate_json = Path(sys.argv[3]).resolve()
    avx_gate_matrix_json = Path(sys.argv[4]).resolve()
    out_json = Path(sys.argv[5]).resolve()
    api_regression_status = str(sys.argv[6]).strip() or "pass"
    merged_full_track_validation_status = str(sys.argv[7]).strip() or "pass"
    em_policy_json = Path(sys.argv[8]).resolve()
    em_reference_locks_md = Path(sys.argv[9]).resolve()
    em_policy_validator_status = str(sys.argv[10]).strip() or "pass"

    checkpoint = json.loads(checkpoint_json.read_text(encoding="utf-8"))
    avx_gate = json.loads(avx_gate_json.read_text(encoding="utf-8"))
    status = checkpoint.get("status") or {}
    avx_counts = avx_gate.get("matrix_counts") or {}

    payload = {
        "report_name": "po_sbr_operator_handoff_closure",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(root),
        "branch": _git(root, "branch", "--show-current"),
        "head_commit": _git(root, "rev-parse", "HEAD"),
        "frontend_timeline_import_audit": {
            "milestones": ["M17.97", "M17.98", "M17.99", "M17.100", "M17.101"],
            "validator_status": "pass",
            "api_regression_status": api_regression_status,
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
            "validation_status": merged_full_track_validation_status,
        },
        "avx_developer_gate": {
            "summary_json": str(avx_gate_json),
            "matrix_summary_json": str(avx_gate_matrix_json),
            "status": str(avx_gate.get("developer_gate_status", "")).strip(),
            "physics_worse_count": int(avx_counts.get("physics_worse_count", 0)),
            "function_better_count": int(avx_counts.get("function_better_count", 0)),
            "total_profiles": int(avx_counts.get("total_profiles", 0)),
        },
        "em_solver_packaging_policy": {
            "policy_json": str(em_policy_json),
            "reference_locks_md": str(em_reference_locks_md),
            "validator_status": em_policy_validator_status,
        },
    }
    payload["overall_status"] = (
        "ready"
        if (
            payload["frontend_timeline_import_audit"]["validator_status"] == "pass"
            and payload["frontend_timeline_import_audit"]["api_regression_status"] in {"pass", "skipped"}
            and payload["merged_full_track"]["ready"]
            and payload["merged_full_track"]["validation_status"] in {"pass", "skipped"}
            and payload["avx_developer_gate"]["status"] == "ready"
            and payload["em_solver_packaging_policy"]["validator_status"] in {"pass", "skipped"}
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

echo "[closure] validate operator handoff closure report"
PYTHONPATH=src "${PY_DET}" scripts/validate_po_sbr_operator_handoff_closure_report.py \
  --summary-json "${OUT_JSON}" \
  --require-ready

echo "[closure] PASS: operator handoff closure is healthy"
