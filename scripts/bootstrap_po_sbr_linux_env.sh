#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${1:-$ROOT_DIR/.venv-po-sbr}"
RTXPY_REPO_PATH="${2:-$ROOT_DIR/external/rtxpy-mod}"
RTXPY_GIT_URL="${RTXPY_GIT_URL:-https://github.com/pingpongballz/rtxpy.git}"
INSTALL_CUPY="${INSTALL_CUPY:-1}"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "[bootstrap] Linux host required."
  exit 2
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "[bootstrap] nvidia-smi not found. NVIDIA runtime is required."
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "[bootstrap] python3 not found."
  exit 2
fi

if ! command -v git >/dev/null 2>&1; then
  echo "[bootstrap] git not found."
  exit 2
fi

echo "[bootstrap] ROOT_DIR=$ROOT_DIR"
echo "[bootstrap] VENV_PATH=$VENV_PATH"
echo "[bootstrap] RTXPY_REPO_PATH=$RTXPY_REPO_PATH"

python3 -m venv "$VENV_PATH"
"$VENV_PATH/bin/python" -m pip install --upgrade pip setuptools wheel cmake
"$VENV_PATH/bin/pip" install numpy matplotlib libigl

if [[ -d "$RTXPY_REPO_PATH/.git" ]]; then
  echo "[bootstrap] updating existing rtxpy repo"
  git -C "$RTXPY_REPO_PATH" pull --ff-only || true
else
  echo "[bootstrap] cloning modified rtxpy repo"
  mkdir -p "$(dirname "$RTXPY_REPO_PATH")"
  git clone "$RTXPY_GIT_URL" "$RTXPY_REPO_PATH"
fi

"$VENV_PATH/bin/pip" install -e "$RTXPY_REPO_PATH"

if [[ "$INSTALL_CUPY" == "1" ]]; then
  if command -v nvcc >/dev/null 2>&1; then
    CUDA_MAJOR="$(nvcc --version | sed -n 's/.*release \([0-9]\+\)\.\([0-9]\+\).*/\1/p' | head -n1)"
    CUPY_PKG=""
    if [[ "$CUDA_MAJOR" == "12" ]]; then
      CUPY_PKG="cupy-cuda12x"
    elif [[ "$CUDA_MAJOR" == "11" ]]; then
      CUPY_PKG="cupy-cuda11x"
    fi
    if [[ -n "$CUPY_PKG" ]]; then
      echo "[bootstrap] installing optional $CUPY_PKG"
      "$VENV_PATH/bin/pip" install "$CUPY_PKG" || echo "[bootstrap] warning: optional $CUPY_PKG install failed"
    else
      echo "[bootstrap] warning: unknown CUDA major '$CUDA_MAJOR'; skipping optional cupy install"
    fi
  else
    echo "[bootstrap] warning: nvcc not found; skipping optional cupy install"
  fi
fi

echo "[bootstrap] completed."
echo "[bootstrap] activate: source \"$VENV_PATH/bin/activate\""
echo "[bootstrap] run strict pilot:"
echo "  bash \"$ROOT_DIR/scripts/run_m14_6_po_sbr_linux_strict.sh\" \\"
echo "    \"$ROOT_DIR/data/runtime_pilot/po_sbr_runtime_pilot_v1\" \\"
echo "    \"$ROOT_DIR/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json\" \\"
echo "    \"$ROOT_DIR/external/PO-SBR-Python\" geometries/plate.obj"
