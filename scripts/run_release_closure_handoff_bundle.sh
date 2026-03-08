#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/3] refresh canonical release-candidate evidence"
PYTHONPATH=src .venv/bin/python scripts/run_canonical_release_candidate_subset.py \
  --output-json docs/reports/canonical_release_candidate_subset_latest.json

echo "[2/3] build release-closure handoff bundle"
python3 scripts/build_release_closure_handoff_bundle.py

echo "[3/3] validate release-closure handoff bundle"
python3 scripts/validate_release_closure_handoff_bundle.py

echo "release-closure handoff bundle: ready"
