#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

OUTPUT_ROOT="${1:-$ROOT_DIR/data/runtime_pilot/po_sbr_runtime_pilot_v1_linux}"
SUMMARY_JSON="${2:-$ROOT_DIR/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json}"
PO_SBR_REPO_ROOT="${3:-$ROOT_DIR/external/PO-SBR-Python}"
GEOMETRY_PATH="${4:-geometries/plate.obj}"

echo "[M14.6] strict PO-SBR runtime pilot start"
echo "  ROOT_DIR=$ROOT_DIR"
echo "  OUTPUT_ROOT=$OUTPUT_ROOT"
echo "  SUMMARY_JSON=$SUMMARY_JSON"
echo "  PO_SBR_REPO_ROOT=$PO_SBR_REPO_ROOT"
echo "  GEOMETRY_PATH=$GEOMETRY_PATH"
echo "  PYTHON_BIN=$PYTHON_BIN"

PYTHONPATH="$ROOT_DIR/src" "$PYTHON_BIN" "$ROOT_DIR/scripts/run_scene_runtime_po_sbr_pilot.py" \
  --output-root "$OUTPUT_ROOT" \
  --output-summary-json "$SUMMARY_JSON" \
  --po-sbr-repo-root "$PO_SBR_REPO_ROOT" \
  --geometry-path "$GEOMETRY_PATH"

PYTHONPATH="$ROOT_DIR/src" "$PYTHON_BIN" "$ROOT_DIR/scripts/validate_scene_runtime_po_sbr_executed_report.py" \
  --summary-json "$SUMMARY_JSON"

echo "[M14.6] strict PO-SBR runtime pilot completed"
