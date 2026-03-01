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

echo "[myproject-checkpoint] start run_id=${RUN_ID}"
echo "[myproject-checkpoint] python=${PY_BIN}"
echo "[myproject-checkpoint] function_test_json=${FUNCTION_TEST_JSON}"
echo "[myproject-checkpoint] local_ready_json=${LOCAL_READY_JSON}"
echo "[myproject-checkpoint] baseline_manifest_json=${BASELINE_MANIFEST_JSON}"

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

echo "[myproject-checkpoint] write checkpoint summary report"
PYTHONPATH=src "${PY_BIN}" - "${ROOT_DIR}" "${RUN_ID}" "${FUNCTION_TEST_JSON}" "${BUNDLE_JSON}" "${GATE_LOCK_JSON}" "${LOCAL_READY_JSON}" "${BASELINE_MANIFEST_JSON}" "${DRIFT_JSON}" "${CHECKPOINT_JSON}" <<'PY'
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    run_id = str(sys.argv[2]).strip()
    function_test_json = Path(sys.argv[3]).resolve()
    bundle_json = Path(sys.argv[4]).resolve()
    gate_lock_json = Path(sys.argv[5]).resolve()
    local_ready_json = Path(sys.argv[6]).resolve()
    baseline_manifest_json = Path(sys.argv[7]).resolve()
    drift_json = Path(sys.argv[8]).resolve()
    out_json = Path(sys.argv[9]).resolve()

    report = {
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
        "overall_status": "ready",
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {out_json}")
    print("overall_status=ready")


if __name__ == "__main__":
    main()
PY

echo "[myproject-checkpoint] done"
echo "[myproject-checkpoint] checkpoint_json=${CHECKPOINT_JSON}"
echo "[myproject-checkpoint] drift_json=${DRIFT_JSON}"
