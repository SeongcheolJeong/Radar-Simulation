#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8080}"
SUMMARY_REL="docs/reports/frontend_quickstart_v1.json"

if [[ -n "${PY_BIN:-}" ]]; then
  PYTHON_BIN="${PY_BIN}"
elif [[ -x "${ROOT_DIR}/.venv-sionna311/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv-sionna311/bin/python"
else
  PYTHON_BIN="$(command -v python3)"
fi

echo "[1/2] Building frontend demo artifacts..."
PYTHONPATH="${ROOT_DIR}/src" "${PYTHON_BIN}" "${ROOT_DIR}/scripts/build_frontend_demo_example.py" \
  --output-root "${ROOT_DIR}/data/demo/frontend_quickstart_v1" \
  --summary-json "${ROOT_DIR}/${SUMMARY_REL}"

URL="http://localhost:${PORT}/frontend/avx_like_dashboard.html?summary=/${SUMMARY_REL}"

echo "[2/2] Starting static server..."
echo "  URL: ${URL}"
echo "  Stop: Ctrl+C"

cd "${ROOT_DIR}"
python3 -m http.server "${PORT}"
