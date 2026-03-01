#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "${ROOT_DIR}"

HOOK_PATH=".githooks/pre-push"

if [[ ! -f "${HOOK_PATH}" ]]; then
  echo "[install-hook] error: missing ${HOOK_PATH}" >&2
  exit 1
fi

chmod +x "${HOOK_PATH}"
git config core.hooksPath .githooks

echo "[install-hook] core.hooksPath=$(git config --get core.hooksPath)"
echo "[install-hook] installed ${HOOK_PATH}"

