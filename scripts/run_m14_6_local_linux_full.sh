#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH_DEFAULT="$ROOT_DIR/.venv-po-sbr"
PYTHON_BIN_DEFAULT="$VENV_PATH_DEFAULT/bin/python"

VENV_PATH="${VENV_PATH:-$VENV_PATH_DEFAULT}"
PYTHON_BIN="${PYTHON_BIN:-$PYTHON_BIN_DEFAULT}"
OUTPUT_ROOT="${OUTPUT_ROOT:-$ROOT_DIR/data/runtime_pilot/po_sbr_runtime_pilot_v1_local_$(date +%Y_%m_%d)}"
SUMMARY_JSON="${SUMMARY_JSON:-$ROOT_DIR/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux_local_$(date +%Y_%m_%d).json}"
CLOSURE_JSON="${CLOSURE_JSON:-$ROOT_DIR/docs/reports/m14_6_closure_readiness_linux_local_$(date +%Y_%m_%d).json}"
PO_SBR_REPO_ROOT="${PO_SBR_REPO_ROOT:-$ROOT_DIR/external/PO-SBR-Python}"
PO_SBR_REPO_URL="${PO_SBR_REPO_URL:-https://github.com/pingpongballz/PO-SBR-Python.git}"
RTXPY_SRC="${RTXPY_SRC:-$ROOT_DIR/external/rtxpy-mod}"
GEOMETRY_PATH="${GEOMETRY_PATH:-geometries/plate.obj}"
SKIP_BOOTSTRAP=0
APPLY_FINALIZE=1

usage() {
  cat <<'EOF'
Usage:
  bash scripts/run_m14_6_local_linux_full.sh [options]

Options:
  --skip-bootstrap           Skip Linux bootstrap step.
  --no-apply-finalize        Skip finalize --apply doc update step.
  --venv-path /abs/path      Python venv path for PO-SBR runtime.
  --python-bin /abs/path     Python executable for pilot/closure/finalize.
  --output-root /abs/path    Output root for generated runtime artifacts.
  --summary-json /abs/path   Strict pilot summary json path.
  --closure-json /abs/path   Closure readiness summary json path.
  --po-sbr-repo /abs/path    PO-SBR-Python repository root.
  --po-sbr-repo-url URL      PO-SBR-Python clone URL when repo path is missing.
  --rtxpy-src /abs/path      rtxpy modified source path for bootstrap.
  --geometry-path path       Geometry path passed to PO-SBR solver.
  -h, --help                 Show help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-bootstrap)
      SKIP_BOOTSTRAP=1
      shift
      ;;
    --no-apply-finalize)
      APPLY_FINALIZE=0
      shift
      ;;
    --venv-path)
      VENV_PATH="$2"
      shift 2
      ;;
    --python-bin)
      PYTHON_BIN="$2"
      shift 2
      ;;
    --output-root)
      OUTPUT_ROOT="$2"
      shift 2
      ;;
    --summary-json)
      SUMMARY_JSON="$2"
      shift 2
      ;;
    --closure-json)
      CLOSURE_JSON="$2"
      shift 2
      ;;
    --po-sbr-repo)
      PO_SBR_REPO_ROOT="$2"
      shift 2
      ;;
    --po-sbr-repo-url)
      PO_SBR_REPO_URL="$2"
      shift 2
      ;;
    --rtxpy-src)
      RTXPY_SRC="$2"
      shift 2
      ;;
    --geometry-path)
      GEOMETRY_PATH="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[local] unknown argument: $1"
      usage
      exit 2
      ;;
  esac
done

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "[local] nvidia-smi not found; Linux+NVIDIA runtime is required for strict PO-SBR execution."
  exit 2
fi

if [[ "$SKIP_BOOTSTRAP" -ne 1 ]]; then
  echo "[local] bootstrap start"
  bash "$ROOT_DIR/scripts/bootstrap_po_sbr_linux_env.sh" "$VENV_PATH" "$RTXPY_SRC"
fi

if [[ ! -d "$PO_SBR_REPO_ROOT" ]]; then
  echo "[local] PO-SBR repo missing; cloning"
  echo "  PO_SBR_REPO_URL=$PO_SBR_REPO_URL"
  echo "  PO_SBR_REPO_ROOT=$PO_SBR_REPO_ROOT"
  mkdir -p "$(dirname "$PO_SBR_REPO_ROOT")"
  git clone "$PO_SBR_REPO_URL" "$PO_SBR_REPO_ROOT"
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  else
    echo "[local] python executable not found: $PYTHON_BIN"
    exit 2
  fi
fi

echo "[local] run start"
echo "  ROOT_DIR=$ROOT_DIR"
echo "  VENV_PATH=$VENV_PATH"
echo "  PYTHON_BIN=$PYTHON_BIN"
echo "  OUTPUT_ROOT=$OUTPUT_ROOT"
echo "  SUMMARY_JSON=$SUMMARY_JSON"
echo "  CLOSURE_JSON=$CLOSURE_JSON"
echo "  PO_SBR_REPO_ROOT=$PO_SBR_REPO_ROOT"
echo "  PO_SBR_REPO_URL=$PO_SBR_REPO_URL"
echo "  RTXPY_SRC=$RTXPY_SRC"
echo "  GEOMETRY_PATH=$GEOMETRY_PATH"
echo "  APPLY_FINALIZE=$APPLY_FINALIZE"

PYTHON_BIN="$PYTHON_BIN" bash "$ROOT_DIR/scripts/run_m14_6_po_sbr_linux_strict.sh" \
  "$OUTPUT_ROOT" \
  "$SUMMARY_JSON" \
  "$PO_SBR_REPO_ROOT" \
  "$GEOMETRY_PATH"

PYTHONPATH="$ROOT_DIR/src" "$PYTHON_BIN" "$ROOT_DIR/scripts/run_m14_6_closure_readiness.py" \
  --linux-summary-json "$SUMMARY_JSON" \
  --output-summary-json "$CLOSURE_JSON"

if [[ "$APPLY_FINALIZE" -eq 1 ]]; then
  PYTHONPATH="$ROOT_DIR/src" "$PYTHON_BIN" "$ROOT_DIR/scripts/finalize_m14_6_from_linux_report.py" \
    --linux-summary-json "$SUMMARY_JSON" \
    --closure-summary-json "$CLOSURE_JSON" \
    --apply
fi

echo "[local] run completed"
echo "  strict_summary_json=$SUMMARY_JSON"
echo "  closure_summary_json=$CLOSURE_JSON"
