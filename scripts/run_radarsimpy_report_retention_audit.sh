#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ -n "${PY_BIN:-}" ]]; then
  PYTHON_BIN="${PY_BIN}"
elif [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python3)"
fi

REPORTS_ROOT="${REPORTS_ROOT:-docs/reports}"
KEEP_PER_GROUP="${KEEP_PER_GROUP:-8}"
OUTPUT_JSON="${OUTPUT_JSON:-docs/reports/radarsimpy_report_retention_audit_latest.json}"
OUTPUT_MD="${OUTPUT_MD:-docs/reports/radarsimpy_report_retention_audit_latest.md}"
APPLY_MODE="${APPLY_MODE:-0}"

CMD=(
  "${PYTHON_BIN}" scripts/audit_radarsimpy_report_retention.py
  --reports-root "${REPORTS_ROOT}"
  --keep-per-group "${KEEP_PER_GROUP}"
  --output-json "${OUTPUT_JSON}"
  --output-md "${OUTPUT_MD}"
)

if [[ "${APPLY_MODE}" == "1" ]]; then
  CMD+=(--apply)
fi

echo "[1/2] run retention audit"
"${CMD[@]}"

echo "[2/2] validate retention audit script"
"${PYTHON_BIN}" scripts/validate_audit_radarsimpy_report_retention.py

echo "run_radarsimpy_report_retention_audit: done"
echo "  reports_root: ${REPORTS_ROOT}"
echo "  keep_per_group: ${KEEP_PER_GROUP}"
echo "  apply_mode: ${APPLY_MODE}"
echo "  output_json: ${OUTPUT_JSON}"
echo "  output_md: ${OUTPUT_MD}"
