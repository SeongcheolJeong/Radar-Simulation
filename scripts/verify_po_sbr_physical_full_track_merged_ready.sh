#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PY_PO_SBR="${ROOT_DIR}/.venv-po-sbr/bin/python"
PY_DET="${ROOT_DIR}/.venv/bin/python"

GEN_CHECKPOINT_SCRIPT="${ROOT_DIR}/scripts/generate_po_sbr_physical_full_track_merged_checkpoint.py"
CHECKPOINT_JSON="${ROOT_DIR}/docs/reports/po_sbr_physical_full_track_merged_checkpoint_2026_03_01.json"
MATRIX_JSON="${ROOT_DIR}/docs/reports/scene_backend_kpi_scenario_matrix_local_2026_03_01_fresh.json"
BUNDLE_JSON="${ROOT_DIR}/docs/reports/po_sbr_physical_full_track_bundle_local_2026_03_01_fresh.json"
GATE_LOCK_JSON="${ROOT_DIR}/docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01_fresh3.json"
STABILITY_JSON="${ROOT_DIR}/data/runtime_golden_path/po_sbr_physical_full_track_gate_lock_local_2026_03_01_fresh3/stability_campaign/po_sbr_physical_full_track_stability.json"
HARDENING_JSON="${ROOT_DIR}/data/runtime_golden_path/po_sbr_physical_full_track_gate_lock_local_2026_03_01_fresh3/hardening_campaign/po_sbr_realism_threshold_hardening.json"

require_file() {
  local path="$1"
  if [[ ! -f "${path}" ]]; then
    echo "missing required file: ${path}" >&2
    exit 1
  fi
}

if [[ ! -x "${PY_PO_SBR}" ]]; then
  echo "missing python interpreter: ${PY_PO_SBR}" >&2
  exit 1
fi
if [[ ! -x "${PY_DET}" ]]; then
  echo "missing python interpreter: ${PY_DET}" >&2
  exit 1
fi

require_file "${GEN_CHECKPOINT_SCRIPT}"
require_file "${CHECKPOINT_JSON}"
require_file "${MATRIX_JSON}"
require_file "${BUNDLE_JSON}"
require_file "${GATE_LOCK_JSON}"
require_file "${STABILITY_JSON}"
require_file "${HARDENING_JSON}"

echo "[verify] refresh checkpoint"
"${PY_PO_SBR}" "${GEN_CHECKPOINT_SCRIPT}" --output-json "${CHECKPOINT_JSON}"

echo "[verify] checkpoint"
"${PY_PO_SBR}" - <<'PY'
import json
from pathlib import Path

p = Path("docs/reports/po_sbr_physical_full_track_merged_checkpoint_2026_03_01.json")
d = json.loads(p.read_text(encoding="utf-8"))
ready = bool(d.get("ready", False))
if not ready:
    raise SystemExit("checkpoint ready=false")
status = d.get("status") or {}
print("  ready:", ready)
print("  matrix_status:", status.get("matrix_status"))
print("  full_track_status:", status.get("full_track_status"))
print("  gate_lock_status:", status.get("gate_lock_status"))
print("  realism_gate_candidate_status:", status.get("realism_gate_candidate_status"))
PY

echo "[verify] matrix/bundle/gate-lock reports"
PYTHONPATH=src "${PY_PO_SBR}" scripts/validate_scene_backend_kpi_scenario_matrix_report.py \
  --summary-json "${MATRIX_JSON}" \
  --require-ready
PYTHONPATH=src "${PY_PO_SBR}" scripts/validate_po_sbr_physical_full_track_bundle_report.py \
  --summary-json "${BUNDLE_JSON}" \
  --require-ready
PYTHONPATH=src "${PY_PO_SBR}" scripts/validate_po_sbr_physical_full_track_stability_report.py \
  --summary-json "${STABILITY_JSON}" \
  --require-stable
PYTHONPATH=src "${PY_PO_SBR}" scripts/validate_po_sbr_realism_threshold_hardening_report.py \
  --summary-json "${HARDENING_JSON}" \
  --require-hardened
PYTHONPATH=src "${PY_PO_SBR}" scripts/validate_po_sbr_physical_full_track_gate_lock_report.py \
  --summary-json "${GATE_LOCK_JSON}" \
  --require-ready

echo "[verify] deterministic runner guards"
PYTHONPATH=src "${PY_DET}" scripts/validate_run_po_sbr_physical_full_track_bundle.py
PYTHONPATH=src "${PY_DET}" scripts/validate_run_po_sbr_physical_full_track_stability_campaign.py
PYTHONPATH=src "${PY_DET}" scripts/validate_run_po_sbr_realism_threshold_hardening_campaign.py
PYTHONPATH=src "${PY_DET}" scripts/validate_run_po_sbr_physical_full_track_gate_lock.py

echo "[verify] PASS: merged full-track readiness is healthy"
