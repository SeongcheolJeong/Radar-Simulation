#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_ROOT="/home/seongcheoljeong/workspace/myproject"
BUNDLE_REL_DIR=""
NAMESPACE_TO=""

usage() {
  cat <<'EOF'
Usage:
  bash scripts/export_po_sbr_migration_bundle.sh [--target-root /abs/path] [--bundle-rel-dir rel/path] [--namespace-to myproject]

Options:
  --target-root    Target repository root. Default: /home/seongcheoljeong/workspace/myproject
  --bundle-rel-dir Relative bundle path in target root.
                   Default: migration_bundles/po_sbr_m14_6_<timestamp>
  --namespace-to   Optional namespace rewrite target for copied python files (from avxsim -> value).
                   Example: --namespace-to myproject
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-root)
      TARGET_ROOT="$2"
      shift 2
      ;;
    --bundle-rel-dir)
      BUNDLE_REL_DIR="$2"
      shift 2
      ;;
    --namespace-to)
      NAMESPACE_TO="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[bundle] unknown argument: $1"
      usage
      exit 2
      ;;
  esac
done

if [[ ! -d "$TARGET_ROOT" ]]; then
  echo "[bundle] target root does not exist: $TARGET_ROOT"
  exit 2
fi

if [[ -z "$BUNDLE_REL_DIR" ]]; then
  BUNDLE_REL_DIR="migration_bundles/po_sbr_m14_6_$(date +%Y%m%d_%H%M%S)"
fi

BUNDLE_ROOT="$TARGET_ROOT/$BUNDLE_REL_DIR"

FILES=(
  "src/avxsim/runtime_providers/po_sbr_rt_provider.py"
  "src/avxsim/adapters/po_sbr_paths.py"
  "scripts/run_scene_runtime_po_sbr_pilot.py"
  "scripts/run_m14_6_po_sbr_linux_strict.sh"
  "scripts/validate_scene_runtime_po_sbr_executed_report.py"
  "scripts/bootstrap_po_sbr_linux_env.sh"
  "scripts/run_m14_6_local_linux_full.sh"
  "scripts/run_m14_6_closure_readiness.py"
  "scripts/finalize_m14_6_from_linux_report.py"
  "docs/112_scene_runtime_po_sbr_pilot_contract.md"
  "docs/113_po_sbr_linux_runtime_runbook.md"
  "docs/114_m14_6_closure_readiness_contract.md"
)

echo "[bundle] source_root=$ROOT_DIR"
echo "[bundle] target_root=$TARGET_ROOT"
echo "[bundle] bundle_root=$BUNDLE_ROOT"
mkdir -p "$BUNDLE_ROOT"

for rel in "${FILES[@]}"; do
  src="$ROOT_DIR/$rel"
  dst="$BUNDLE_ROOT/$rel"
  if [[ ! -f "$src" ]]; then
    echo "[bundle] missing source file: $src"
    exit 2
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
done

if [[ -n "$NAMESPACE_TO" && "$NAMESPACE_TO" != "avxsim" ]]; then
  echo "[bundle] rewriting namespace avxsim -> $NAMESPACE_TO"
  find "$BUNDLE_ROOT" -type f -name "*.py" -print0 | while IFS= read -r -d '' pyf; do
    sed -i \
      -e "s/from avxsim\\./from ${NAMESPACE_TO}\\./g" \
      -e "s/import avxsim\\./import ${NAMESPACE_TO}\\./g" \
      -e "s/'avxsim\\./'${NAMESPACE_TO}\\./g" \
      -e "s/\"avxsim\\./\"${NAMESPACE_TO}\\./g" \
      "$pyf"
  done
fi

SOURCE_COMMIT="$(git -C "$ROOT_DIR" rev-parse --short HEAD || true)"
cat > "$BUNDLE_ROOT/README_MIGRATION_BUNDLE.md" <<EOF
# PO-SBR Migration Bundle

Exported from:
- source_repo: $ROOT_DIR
- source_commit: $SOURCE_COMMIT
- exported_at: $(date -Iseconds)

Target root:
- $TARGET_ROOT

Bundle path:
- $BUNDLE_ROOT

What is included:
- PO-SBR runtime provider + adapter
- Linux bootstrap/strict pilot/closure scripts
- M14.6 contracts/runbook docs

Suggested integration order:
1. Copy files from this bundle into your active myproject tree.
2. Align python imports/namespace and runtime provider entry string.
3. Run stubbed validations first.
4. Run Linux strict pilot and closure readiness.
EOF

echo "[bundle] export completed"
echo "[bundle] next:"
echo "  cd \"$TARGET_ROOT\""
echo "  find \"$BUNDLE_REL_DIR\" -type f | sort"
