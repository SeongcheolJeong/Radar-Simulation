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

PACK_JSON="${PACK_JSON:-docs/reports/release_announcement_pack_latest.json}"
PACK_MD="${PACK_MD:-docs/reports/release_announcement_pack_latest.md}"
RELEASE_DATE="${RELEASE_DATE:-2026-03-05}"

echo "[1/2] build release announcement pack"
"${PYTHON_BIN}" scripts/build_release_announcement_pack.py \
  --release-date "${RELEASE_DATE}" \
  --output-json "${PACK_JSON}" \
  --output-md "${PACK_MD}"

echo "[2/2] validate release announcement pack"
"${PYTHON_BIN}" scripts/validate_release_announcement_pack.py \
  --pack-json "${PACK_JSON}" \
  --repo-root "${ROOT_DIR}"

echo "run_release_announcement_pack: done"
echo "  pack_json: ${PACK_JSON}"
echo "  pack_md: ${PACK_MD}"

