#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UI_PORT="${1:-8080}"
API_PORT="${2:-8099}"
SUMMARY_REL="docs/reports/frontend_quickstart_v1.json"
SCENE_REL="data/demo/frontend_quickstart_v1/scene_frontend_quickstart.json"

if [[ -n "${PY_BIN:-}" ]]; then
  PYTHON_BIN="${PY_BIN}"
elif [[ -x "${ROOT_DIR}/.venv-sionna311/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv-sionna311/bin/python"
else
  PYTHON_BIN="$(command -v python3)"
fi

URL="http://localhost:${UI_PORT}/frontend/avx_like_dashboard.html?summary=/${SUMMARY_REL}&api=http://127.0.0.1:${API_PORT}&scene=${SCENE_REL}&profile=fast_debug"

echo "[1/3] Building frontend demo fixtures..."
PYTHONPATH="${ROOT_DIR}/src" "${PYTHON_BIN}" "${ROOT_DIR}/scripts/build_frontend_demo_example.py" \
  --output-root "${ROOT_DIR}/data/demo/frontend_quickstart_v1" \
  --summary-json "${ROOT_DIR}/${SUMMARY_REL}"

echo "[2/3] Starting Web E2E API on :${API_PORT} ..."
PYTHONPATH="${ROOT_DIR}/src" "${PYTHON_BIN}" "${ROOT_DIR}/scripts/run_web_e2e_orchestrator_api.py" \
  --host 127.0.0.1 \
  --port "${API_PORT}" \
  --repo-root "${ROOT_DIR}" \
  --store-root "${ROOT_DIR}/data/web_e2e" \
  > /tmp/web_e2e_api_${API_PORT}.log 2>&1 &
API_PID=$!

cleanup() {
  if kill -0 "${API_PID}" >/dev/null 2>&1; then
    kill "${API_PID}" >/dev/null 2>&1 || true
    wait "${API_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

sleep 1
if ! kill -0 "${API_PID}" >/dev/null 2>&1; then
  echo "api failed to start. check: /tmp/web_e2e_api_${API_PORT}.log"
  exit 1
fi

echo "[3/3] Starting static server on :${UI_PORT} ..."
echo "  Dashboard URL: ${URL}"
echo "  API log: /tmp/web_e2e_api_${API_PORT}.log"
echo "  Stop: Ctrl+C"

cd "${ROOT_DIR}"
python3 -m http.server "${UI_PORT}"
