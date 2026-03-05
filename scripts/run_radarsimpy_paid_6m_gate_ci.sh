#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PY_BIN="${PY_BIN:-${ROOT_DIR}/.venv/bin/python}"
if [[ ! -x "${PY_BIN}" ]]; then
  echo "python binary not found: ${PY_BIN}" >&2
  exit 1
fi

RADARSIMPY_PACKAGE_ROOT="${RADARSIMPY_PACKAGE_ROOT:-${ROOT_DIR}/external/radarsimpy_order_pull_latest/extracted/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU}"
RADARSIMPY_LIBCOMPAT_DIR="${RADARSIMPY_LIBCOMPAT_DIR:-${ROOT_DIR}/external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu}"
RADARSIMPY_LICENSE_FILE="${RADARSIMPY_LICENSE_FILE:-/home/seongcheoljeong/Documents/license_RadarSimPy_10760.lic}"
REPORTS_ROOT="${REPORTS_ROOT:-${ROOT_DIR}/docs/reports}"

if [[ ! -d "${RADARSIMPY_PACKAGE_ROOT}" ]]; then
  echo "RADARSIMPY_PACKAGE_ROOT not found: ${RADARSIMPY_PACKAGE_ROOT}" >&2
  exit 1
fi
if [[ ! -d "${RADARSIMPY_LIBCOMPAT_DIR}" ]]; then
  echo "RADARSIMPY_LIBCOMPAT_DIR not found: ${RADARSIMPY_LIBCOMPAT_DIR}" >&2
  exit 1
fi
if [[ ! -f "${RADARSIMPY_LICENSE_FILE}" ]]; then
  echo "RADARSIMPY_LICENSE_FILE not found: ${RADARSIMPY_LICENSE_FILE}" >&2
  exit 1
fi

export PYTHONPATH="src:${RADARSIMPY_PACKAGE_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
export LD_LIBRARY_PATH="${RADARSIMPY_LIBCOMPAT_DIR}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export RADARSIMPY_LICENSE_FILE

mkdir -p "${REPORTS_ROOT}"

echo "[1/3] production release gate"
"${PY_BIN}" scripts/run_radarsimpy_production_release_gate.py \
  --license-file "${RADARSIMPY_LICENSE_FILE}" \
  --trial-package-root "${RADARSIMPY_PACKAGE_ROOT}" \
  --libcompat-dir "${RADARSIMPY_LIBCOMPAT_DIR}" \
  --output-json "${REPORTS_ROOT}/radarsimpy_production_release_gate_paid_6m.json"

echo "[2/3] readiness checkpoint"
"${PY_BIN}" scripts/run_radarsimpy_readiness_checkpoint.py \
  --with-real-runtime \
  --runtime-license-tier production \
  --trial-package-root "${RADARSIMPY_PACKAGE_ROOT}" \
  --libcompat-dir "${RADARSIMPY_LIBCOMPAT_DIR}" \
  --license-file "${RADARSIMPY_LICENSE_FILE}" \
  --output-json "${REPORTS_ROOT}/radarsimpy_readiness_checkpoint_paid_6m.json"

echo "[3/3] simulator reference parity"
"${PY_BIN}" scripts/validate_radarsimpy_simulator_reference_parity_optional.py \
  --require-runtime \
  --output-json "${REPORTS_ROOT}/radarsimpy_simulator_reference_parity_paid_6m.json"

echo "run_radarsimpy_paid_6m_gate_ci: done"

