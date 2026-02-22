#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SSH_HOST=""
REMOTE_REPO=""
SSH_PORT=""
IDENTITY_FILE=""
SKIP_BOOTSTRAP=0
APPLY_FINALIZE_LOCAL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ssh-host)
      SSH_HOST="$2"; shift 2 ;;
    --remote-repo)
      REMOTE_REPO="$2"; shift 2 ;;
    --ssh-port)
      SSH_PORT="$2"; shift 2 ;;
    --identity-file)
      IDENTITY_FILE="$2"; shift 2 ;;
    --skip-bootstrap)
      SKIP_BOOTSTRAP=1; shift 1 ;;
    --apply-finalize-local)
      APPLY_FINALIZE_LOCAL=1; shift 1 ;;
    *)
      echo "[remote] unknown argument: $1"
      exit 2 ;;
  esac
done

if [[ -z "$SSH_HOST" || -z "$REMOTE_REPO" ]]; then
  echo "Usage:"
  echo "  bash scripts/run_m14_6_remote_linux_over_ssh.sh --ssh-host user@host --remote-repo /abs/path/to/Codex_test [--ssh-port 22] [--identity-file ~/.ssh/id_rsa] [--skip-bootstrap] [--apply-finalize-local]"
  exit 2
fi

SSH_CMD=(ssh -o BatchMode=yes)
SCP_CMD=(scp -q)
if [[ -n "$SSH_PORT" ]]; then
  SSH_CMD+=(-p "$SSH_PORT")
  SCP_CMD+=(-P "$SSH_PORT")
fi
if [[ -n "$IDENTITY_FILE" ]]; then
  SSH_CMD+=(-i "$IDENTITY_FILE")
  SCP_CMD+=(-i "$IDENTITY_FILE")
fi

REMOTE_PY="$REMOTE_REPO/.venv-po-sbr/bin/python"
REMOTE_SUMMARY="$REMOTE_REPO/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json"
REMOTE_CLOSURE="$REMOTE_REPO/docs/reports/m14_6_closure_readiness_linux.json"

LOCAL_SUMMARY="$ROOT_DIR/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json"
LOCAL_CLOSURE="$ROOT_DIR/docs/reports/m14_6_closure_readiness_linux.json"

run_remote() {
  local cmd="$1"
  "${SSH_CMD[@]}" "$SSH_HOST" "set -euo pipefail; $cmd"
}

echo "[remote] host=$SSH_HOST"
echo "[remote] remote_repo=$REMOTE_REPO"

run_remote "test -d \"$REMOTE_REPO\" && test -f \"$REMOTE_REPO/scripts/run_m14_6_po_sbr_linux_strict.sh\""

if [[ "$SKIP_BOOTSTRAP" == "0" ]]; then
  echo "[remote] bootstrap start"
  run_remote "bash \"$REMOTE_REPO/scripts/bootstrap_po_sbr_linux_env.sh\" \"$REMOTE_REPO/.venv-po-sbr\" \"$REMOTE_REPO/external/rtxpy-mod\""
fi

echo "[remote] strict pilot start"
run_remote "PYTHON_BIN=\"$REMOTE_PY\" bash \"$REMOTE_REPO/scripts/run_m14_6_po_sbr_linux_strict.sh\" \"$REMOTE_REPO/data/runtime_pilot/po_sbr_runtime_pilot_v1\" \"$REMOTE_SUMMARY\" \"$REMOTE_REPO/external/PO-SBR-Python\" geometries/plate.obj"

echo "[remote] closure readiness check"
run_remote "PYTHONPATH=\"$REMOTE_REPO/src\" \"$REMOTE_PY\" \"$REMOTE_REPO/scripts/run_m14_6_closure_readiness.py\" --linux-summary-json \"$REMOTE_SUMMARY\" --output-summary-json \"$REMOTE_CLOSURE\""

mkdir -p "$ROOT_DIR/docs/reports"

echo "[remote] downloading reports"
"${SCP_CMD[@]}" "$SSH_HOST:$REMOTE_SUMMARY" "$LOCAL_SUMMARY"
"${SCP_CMD[@]}" "$SSH_HOST:$REMOTE_CLOSURE" "$LOCAL_CLOSURE"

echo "[remote] local report paths:"
echo "  $LOCAL_SUMMARY"
echo "  $LOCAL_CLOSURE"

if [[ "$APPLY_FINALIZE_LOCAL" == "1" ]]; then
  echo "[remote] applying local finalize"
  PYTHONPATH="$ROOT_DIR/src" python3 "$ROOT_DIR/scripts/finalize_m14_6_from_linux_report.py" \
    --linux-summary-json "$LOCAL_SUMMARY" \
    --closure-summary-json "$LOCAL_CLOSURE" \
    --apply
fi

echo "[remote] done"
