#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "${ROOT_DIR}"

DATE_STAMP="${1:-$(date -u +%Y_%m_%d)}"
HEAD_SHORT="$(git rev-parse --short HEAD)"
RUN_ID="${DATE_STAMP}_${HEAD_SHORT}"

PY_BIN=""
for candidate in \
  "${ROOT_DIR}/.venv-po-sbr/bin/python" \
  "${ROOT_DIR}/.venv/bin/python" \
  "python3"; do
  if [[ "${candidate}" == "python3" ]]; then
    if command -v python3 >/dev/null 2>&1; then
      PY_BIN="python3"
      break
    fi
  elif [[ -x "${candidate}" ]]; then
    PY_BIN="${candidate}"
    break
  fi
done

if [[ -z "${PY_BIN}" ]]; then
  echo "[myproject-checkpoint] error: python runtime not found (.venv-po-sbr/.venv/python3)" >&2
  exit 1
fi

_latest_report() {
  local pattern="$1"
  local latest
  latest="$(ls -1t ${pattern} 2>/dev/null | head -n 1 || true)"
  if [[ -z "${latest}" ]]; then
    return 1
  fi
  printf "%s\n" "${latest}"
}

FUNCTION_TEST_JSON="${PO_SBR_FUNCTION_TEST_JSON_OVERRIDE:-}"
if [[ -z "${FUNCTION_TEST_JSON}" ]]; then
  FUNCTION_TEST_JSON="$(_latest_report "docs/reports/po_sbr_physical_full_track_function_test_*.json")"
fi
if [[ -z "${FUNCTION_TEST_JSON}" || ! -f "${FUNCTION_TEST_JSON}" ]]; then
  echo "[myproject-checkpoint] error: function-test summary not found" >&2
  exit 1
fi

LOCAL_READY_JSON="${PO_SBR_LOCAL_READY_SUMMARY_JSON_OVERRIDE:-}"
if [[ -z "${LOCAL_READY_JSON}" ]]; then
  LOCAL_READY_JSON="$(_latest_report "docs/reports/po_sbr_local_ready_regression_*.json")"
fi
if [[ -z "${LOCAL_READY_JSON}" || ! -f "${LOCAL_READY_JSON}" ]]; then
  echo "[myproject-checkpoint] error: local-ready summary not found" >&2
  exit 1
fi

BASELINE_MANIFEST_JSON="${PO_SBR_BASELINE_MANIFEST_JSON_OVERRIDE:-docs/reports/baselines/po_sbr_local_ready_2026_03_01_pc_self/baseline_manifest.json}"
if [[ ! -f "${BASELINE_MANIFEST_JSON}" ]]; then
  echo "[myproject-checkpoint] error: baseline manifest not found: ${BASELINE_MANIFEST_JSON}" >&2
  exit 1
fi

DRIFT_JSON="docs/reports/po_sbr_local_ready_baseline_drift_checkpoint_${RUN_ID}.json"
CHECKPOINT_JSON="docs/reports/po_sbr_myproject_readiness_checkpoint_${RUN_ID}.json"
PROGRESS_JSON="docs/reports/po_sbr_progress_snapshot_${RUN_ID}.json"
AVX_GATE_JSON="${PO_SBR_AVX_DEVELOPER_GATE_SUMMARY_JSON_OVERRIDE:-docs/reports/po_sbr_avx_developer_gate_${DATE_STAMP}.json}"
AVX_GATE_MATRIX_JSON="${PO_SBR_AVX_DEVELOPER_GATE_MATRIX_SUMMARY_JSON_OVERRIDE:-docs/reports/avx_export_benchmark_matrix_${DATE_STAMP}_developer_gate/summary.json}"
EM_POLICY_JSON="${PO_SBR_EM_POLICY_JSON_OVERRIDE:-docs/em_solver_packaging_policy.json}"
EM_REFERENCE_LOCKS_MD="${PO_SBR_EM_REFERENCE_LOCKS_MD_OVERRIDE:-external/reference-locks.md}"

echo "[myproject-checkpoint] start run_id=${RUN_ID}"
echo "[myproject-checkpoint] python=${PY_BIN}"
echo "[myproject-checkpoint] function_test_json=${FUNCTION_TEST_JSON}"
echo "[myproject-checkpoint] local_ready_json=${LOCAL_READY_JSON}"
echo "[myproject-checkpoint] baseline_manifest_json=${BASELINE_MANIFEST_JSON}"
echo "[myproject-checkpoint] avx_gate_json=${AVX_GATE_JSON}"
echo "[myproject-checkpoint] avx_gate_matrix_json=${AVX_GATE_MATRIX_JSON}"
echo "[myproject-checkpoint] em_policy_json=${EM_POLICY_JSON}"
echo "[myproject-checkpoint] em_reference_locks_md=${EM_REFERENCE_LOCKS_MD}"

mapfile -t _function_meta < <(
  PYTHONPATH=src "${PY_BIN}" - "${FUNCTION_TEST_JSON}" <<'PY'
import json
import sys
from pathlib import Path

summary = Path(sys.argv[1]).expanduser().resolve()
payload = json.loads(summary.read_text(encoding="utf-8"))
if not isinstance(payload, dict):
    raise SystemExit("function-test summary must be object")

overall_status = str(payload.get("overall_status", "")).strip()
bundle_json = str(payload.get("bundle_summary_json", "")).strip()
gate_lock_json = str(payload.get("gate_lock_summary_json", "")).strip()

if overall_status != "ready":
    raise SystemExit(f"function-test overall_status is not ready: {overall_status}")
if bundle_json == "" or gate_lock_json == "":
    raise SystemExit("function-test summary missing bundle/gate-lock summary paths")
if not Path(bundle_json).exists():
    raise SystemExit(f"bundle summary missing: {bundle_json}")
if not Path(gate_lock_json).exists():
    raise SystemExit(f"gate-lock summary missing: {gate_lock_json}")

print(str(Path(bundle_json).resolve()))
print(str(Path(gate_lock_json).resolve()))
print(overall_status)
PY
)

if [[ "${#_function_meta[@]}" -lt 3 ]]; then
  echo "[myproject-checkpoint] error: failed to parse function-test metadata" >&2
  exit 1
fi

BUNDLE_JSON="${_function_meta[0]}"
GATE_LOCK_JSON="${_function_meta[1]}"

echo "[myproject-checkpoint] validate bundle report"
PYTHONPATH=src "${PY_BIN}" scripts/validate_po_sbr_physical_full_track_bundle_report.py \
  --summary-json "${BUNDLE_JSON}" \
  --require-ready

echo "[myproject-checkpoint] validate gate-lock report"
PYTHONPATH=src "${PY_BIN}" scripts/validate_po_sbr_physical_full_track_gate_lock_report.py \
  --summary-json "${GATE_LOCK_JSON}" \
  --require-ready

echo "[myproject-checkpoint] validate local-ready regression report"
PYTHONPATH=src "${PY_BIN}" scripts/validate_po_sbr_local_ready_regression_report.py \
  --summary-json "${LOCAL_READY_JSON}" \
  --require-ready

echo "[myproject-checkpoint] baseline drift check (current candidate vs frozen baseline)"
PYTHONPATH=src "${PY_BIN}" scripts/check_po_sbr_local_ready_baseline_drift.py \
  --baseline-manifest-json "${BASELINE_MANIFEST_JSON}" \
  --candidate-summary-json "${LOCAL_READY_JSON}" \
  --output-json "${DRIFT_JSON}" \
  --require-match \
  --require-candidate-ready

echo "[myproject-checkpoint] validate baseline drift report"
PYTHONPATH=src "${PY_BIN}" scripts/validate_po_sbr_local_ready_baseline_drift_report.py \
  --report-json "${DRIFT_JSON}" \
  --require-match

echo "[myproject-checkpoint] run AVX developer strict gate"
PYTHONPATH=src "${PY_BIN}" scripts/run_po_sbr_avx_developer_gate.py \
  --matrix-summary-json "${AVX_GATE_MATRIX_JSON}" \
  --output-summary-json "${AVX_GATE_JSON}" \
  --strict-ready

echo "[myproject-checkpoint] validate AVX developer gate report"
PYTHONPATH=src "${PY_BIN}" scripts/validate_po_sbr_avx_developer_gate_report.py \
  --summary-json "${AVX_GATE_JSON}" \
  --require-ready \
  --require-function-better-all \
  --min-physics-better-count 1

EM_POLICY_VALIDATOR_STATUS="skipped"
if [[ "${PO_SBR_SKIP_EM_POLICY_VALIDATOR:-0}" != "1" ]]; then
  echo "[myproject-checkpoint] validate EM solver packaging policy"
  PYTHONPATH=src "${PY_BIN}" scripts/validate_em_solver_packaging_policy.py \
    --policy-json "${EM_POLICY_JSON}" \
    --reference-locks-md "${EM_REFERENCE_LOCKS_MD}"
  EM_POLICY_VALIDATOR_STATUS="pass"
else
  echo "[myproject-checkpoint] skip EM solver packaging policy validator (PO_SBR_SKIP_EM_POLICY_VALIDATOR=1)"
fi

POST_CHANGE_GATE_VALIDATOR_STATUS="skipped"
if [[ "${PO_SBR_SKIP_POST_CHANGE_GATE_VALIDATOR:-0}" != "1" ]]; then
  echo "[myproject-checkpoint] validate post-change deterministic gate"
  PYTHONPATH=src "${PY_BIN}" scripts/validate_run_po_sbr_post_change_gate.py
  POST_CHANGE_GATE_VALIDATOR_STATUS="pass"
else
  echo "[myproject-checkpoint] skip post-change deterministic validator (PO_SBR_SKIP_POST_CHANGE_GATE_VALIDATOR=1)"
fi

CLOSURE_REPORT_VALIDATOR_STATUS="skipped"
if [[ "${PO_SBR_SKIP_CLOSURE_REPORT_VALIDATOR:-0}" != "1" ]]; then
  echo "[myproject-checkpoint] validate operator-closure report deterministic runner"
  PYTHONPATH=src "${PY_BIN}" scripts/validate_run_po_sbr_operator_handoff_closure_report.py
  CLOSURE_REPORT_VALIDATOR_STATUS="pass"
else
  echo "[myproject-checkpoint] skip operator-closure report deterministic validator (PO_SBR_SKIP_CLOSURE_REPORT_VALIDATOR=1)"
fi

echo "[myproject-checkpoint] progress snapshot"
PYTHONPATH=src "${PY_BIN}" scripts/show_po_sbr_progress.py \
  --strict-ready \
  --output-json "${PROGRESS_JSON}"

PROGRESS_SNAPSHOT_VALIDATOR_STATUS="skipped"
if [[ "${PO_SBR_SKIP_PROGRESS_SNAPSHOT_VALIDATOR:-0}" != "1" ]]; then
  echo "[myproject-checkpoint] validate progress snapshot deterministic runner"
  PYTHONPATH=src "${PY_BIN}" scripts/validate_run_po_sbr_progress_snapshot.py
  PROGRESS_SNAPSHOT_VALIDATOR_STATUS="pass"
else
  echo "[myproject-checkpoint] skip progress snapshot deterministic validator (PO_SBR_SKIP_PROGRESS_SNAPSHOT_VALIDATOR=1)"
fi

HOOK_SELFTEST_VALIDATOR_STATUS="skipped"
if [[ "${PO_SBR_SKIP_HOOK_SELFTEST:-0}" != "1" ]]; then
  echo "[myproject-checkpoint] validate pre-push local-artifact mode"
  PYTHONPATH=src "${PY_BIN}" scripts/validate_po_sbr_pre_push_hook_local_artifacts.py
  HOOK_SELFTEST_VALIDATOR_STATUS="pass"
else
  echo "[myproject-checkpoint] skip pre-push local-artifact validator (PO_SBR_SKIP_HOOK_SELFTEST=1)"
fi

echo "[myproject-checkpoint] write checkpoint summary report"
PYTHONPATH=src "${PY_BIN}" - "${ROOT_DIR}" "${RUN_ID}" "${FUNCTION_TEST_JSON}" "${BUNDLE_JSON}" "${GATE_LOCK_JSON}" "${LOCAL_READY_JSON}" "${BASELINE_MANIFEST_JSON}" "${DRIFT_JSON}" "${AVX_GATE_JSON}" "${AVX_GATE_MATRIX_JSON}" "${EM_POLICY_JSON}" "${EM_REFERENCE_LOCKS_MD}" "${EM_POLICY_VALIDATOR_STATUS}" "${POST_CHANGE_GATE_VALIDATOR_STATUS}" "${CLOSURE_REPORT_VALIDATOR_STATUS}" "${PROGRESS_JSON}" "${PROGRESS_SNAPSHOT_VALIDATOR_STATUS}" "${HOOK_SELFTEST_VALIDATOR_STATUS}" "${CHECKPOINT_JSON}" <<'PY'
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"json object expected: {path}")
    return payload


def _as_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    run_id = str(sys.argv[2]).strip()
    function_test_json = Path(sys.argv[3]).resolve()
    bundle_json = Path(sys.argv[4]).resolve()
    gate_lock_json = Path(sys.argv[5]).resolve()
    local_ready_json = Path(sys.argv[6]).resolve()
    baseline_manifest_json = Path(sys.argv[7]).resolve()
    drift_json = Path(sys.argv[8]).resolve()
    avx_gate_json = Path(sys.argv[9]).resolve()
    avx_gate_matrix_json = Path(sys.argv[10]).resolve()
    em_policy_json = Path(sys.argv[11]).resolve()
    em_reference_locks_md = Path(sys.argv[12]).resolve()
    em_policy_validator_status = str(sys.argv[13]).strip()
    post_change_gate_validator_status = str(sys.argv[14]).strip()
    closure_report_validator_status = str(sys.argv[15]).strip()
    progress_snapshot_json = Path(sys.argv[16]).resolve()
    progress_snapshot_validator_status = str(sys.argv[17]).strip()
    hook_selftest_validator_status = str(sys.argv[18]).strip()
    out_json = Path(sys.argv[19]).resolve()

    function_test = _load_json(function_test_json)
    local_ready = _load_json(local_ready_json)
    drift = _load_json(drift_json)
    avx_gate = _load_json(avx_gate_json)
    progress_snapshot = _load_json(progress_snapshot_json)

    function_test_overall_status = str(function_test.get("overall_status", "")).strip()
    local_ready_summary = local_ready.get("summary")
    if isinstance(local_ready_summary, dict):
        local_ready_overall_status = str(local_ready_summary.get("overall_status", "")).strip()
    else:
        local_ready_overall_status = str(local_ready.get("overall_status", "")).strip()
    baseline_drift_verdict = str(drift.get("drift_verdict", "")).strip()
    baseline_drift_difference_count = _as_int(drift.get("difference_count", -1), default=-1)
    avx_developer_gate_status = str(avx_gate.get("developer_gate_status", "")).strip()
    progress_snapshot_overall_ready = bool(progress_snapshot.get("overall_ready", False))

    em_policy_validator_ok = em_policy_validator_status in {"pass", "skipped"}
    post_change_gate_validator_ok = post_change_gate_validator_status in {"pass", "skipped"}
    closure_report_validator_ok = closure_report_validator_status in {"pass", "skipped"}
    progress_snapshot_validator_ok = progress_snapshot_validator_status in {"pass", "skipped"}
    hook_selftest_validator_ok = hook_selftest_validator_status in {"pass", "skipped"}
    baseline_drift_ok = (
        baseline_drift_verdict == "match" and baseline_drift_difference_count == 0
    )

    checkpoint_ready = all(
        [
            function_test_overall_status == "ready",
            local_ready_overall_status == "ready",
            baseline_drift_ok,
            avx_developer_gate_status == "ready",
            em_policy_validator_ok,
            post_change_gate_validator_ok,
            closure_report_validator_ok,
            progress_snapshot_overall_ready,
            progress_snapshot_validator_ok,
            hook_selftest_validator_ok,
        ]
    )
    checkpoint_status = "ready" if checkpoint_ready else "blocked"

    report = {
        "version": 1,
        "report_name": "po_sbr_myproject_readiness_checkpoint",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(root),
        "run_id": run_id,
        "branch": _git(root, "branch", "--show-current"),
        "head_commit": _git(root, "rev-parse", "HEAD"),
        "function_test_summary_json": str(function_test_json),
        "bundle_summary_json": str(bundle_json),
        "gate_lock_summary_json": str(gate_lock_json),
        "local_ready_summary_json": str(local_ready_json),
        "baseline_manifest_json": str(baseline_manifest_json),
        "baseline_drift_report_json": str(drift_json),
        "baseline_drift_verdict": baseline_drift_verdict,
        "baseline_drift_difference_count": baseline_drift_difference_count,
        "avx_developer_gate_summary_json": str(avx_gate_json),
        "avx_developer_gate_matrix_summary_json": str(avx_gate_matrix_json),
        "avx_developer_gate_status": avx_developer_gate_status,
        "em_solver_policy_json": str(em_policy_json),
        "em_solver_reference_locks_md": str(em_reference_locks_md),
        "em_policy_validator_status": em_policy_validator_status,
        "post_change_gate_validator_status": post_change_gate_validator_status,
        "closure_report_validator_status": closure_report_validator_status,
        "progress_snapshot_json": str(progress_snapshot_json),
        "progress_snapshot_overall_ready": progress_snapshot_overall_ready,
        "progress_snapshot_validator_status": progress_snapshot_validator_status,
        "hook_selftest_validator_status": hook_selftest_validator_status,
        "function_test_overall_status": function_test_overall_status,
        "local_ready_overall_status": local_ready_overall_status,
        "checkpoint_checks": {
            "function_test_ready": function_test_overall_status == "ready",
            "local_ready_ready": local_ready_overall_status == "ready",
            "baseline_drift_match": baseline_drift_ok,
            "avx_developer_gate_ready": avx_developer_gate_status == "ready",
            "em_policy_validator_ok": em_policy_validator_ok,
            "post_change_gate_validator_ok": post_change_gate_validator_ok,
            "closure_report_validator_ok": closure_report_validator_ok,
            "progress_snapshot_overall_ready": progress_snapshot_overall_ready,
            "progress_snapshot_validator_ok": progress_snapshot_validator_ok,
            "hook_selftest_validator_ok": hook_selftest_validator_ok,
        },
        "overall_status": checkpoint_status,
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {out_json}")
    print(f"overall_status={checkpoint_status}")
    if not checkpoint_ready:
        raise SystemExit("myproject readiness checkpoint is blocked")


if __name__ == "__main__":
    main()
PY

echo "[myproject-checkpoint] validate myproject checkpoint report"
PYTHONPATH=src "${PY_BIN}" scripts/validate_po_sbr_myproject_readiness_checkpoint_report.py \
  --summary-json "${CHECKPOINT_JSON}" \
  --require-ready

echo "[myproject-checkpoint] done"
echo "[myproject-checkpoint] checkpoint_json=${CHECKPOINT_JSON}"
echo "[myproject-checkpoint] drift_json=${DRIFT_JSON}"
echo "[myproject-checkpoint] progress_json=${PROGRESS_JSON}"
