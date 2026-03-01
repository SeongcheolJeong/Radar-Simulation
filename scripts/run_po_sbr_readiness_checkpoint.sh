#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "${ROOT_DIR}"

DATE_STAMP="${1:-$(date -u +%Y_%m_%d)}"

PY_BIN=""
for candidate in \
  "${ROOT_DIR}/.venv/bin/python" \
  "${ROOT_DIR}/.venv-po-sbr/bin/python" \
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
  echo "[checkpoint] error: python runtime not found (.venv/.venv-po-sbr/python3)" >&2
  exit 1
fi

POST_CHANGE_JSON="docs/reports/po_sbr_post_change_gate_${DATE_STAMP}.json"
PROGRESS_JSON="docs/reports/po_sbr_progress_snapshot_${DATE_STAMP}.json"

echo "[checkpoint] start date_stamp=${DATE_STAMP}"
echo "[checkpoint] python=${PY_BIN}"

echo "[checkpoint] verify merged full-track readiness"
bash scripts/verify_po_sbr_physical_full_track_merged_ready.sh

echo "[checkpoint] verify operator handoff closure"
bash scripts/verify_po_sbr_operator_handoff_closure.sh

echo "[checkpoint] force-run post-change gate"
PYTHONPATH=src "${PY_BIN}" scripts/run_po_sbr_post_change_gate.py \
  --force-run \
  --strict \
  --base-ref HEAD~1 \
  --head-ref HEAD \
  --output-json "${POST_CHANGE_JSON}"

echo "[checkpoint] progress snapshot"
PYTHONPATH=src "${PY_BIN}" scripts/show_po_sbr_progress.py \
  --strict-ready \
  --output-json "${PROGRESS_JSON}"

echo "[checkpoint] done"
echo "[checkpoint] post_change_report=${POST_CHANGE_JSON}"
echo "[checkpoint] progress_report=${PROGRESS_JSON}"

