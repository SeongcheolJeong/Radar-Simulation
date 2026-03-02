#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXT_DIR="$ROOT_DIR/external"
GIT_BIN="$(command -v git || true)"
if [[ -z "${GIT_BIN}" ]]; then
  echo "[error] git not found in PATH" >&2
  exit 1
fi

mkdir -p "$EXT_DIR"

clone_if_missing() {
  local name="$1"
  local url="$2"
  local dir="$EXT_DIR/$name"
  if [[ -d "$dir/.git" ]]; then
    echo "[skip] $name already exists: $dir"
    return
  fi
  echo "[clone] $name <- $url"
  "$GIT_BIN" clone --depth 1 "$url" "$dir"
}

clone_if_missing "HybridDynamicRT" "https://github.com/liuy2022/HybridDynamicRT.git"
clone_if_missing "sionna" "https://github.com/NVlabs/sionna.git"
clone_if_missing "radarsimpy" "https://github.com/radarsimx/radarsimpy.git"
clone_if_missing "Raw_ADC_radar_dataset_for_automotive_object_detection" "https://github.com/Xiangyu-Gao/Raw_ADC_radar_dataset_for_automotive_object_detection.git"
clone_if_missing "openEMS" "https://github.com/thliebig/openEMS.git"
clone_if_missing "CSXCAD" "https://github.com/thliebig/CSXCAD.git"
clone_if_missing "gprMax" "https://github.com/gprMax/gprMax.git"

date_str="$(date +%F)"
hybrid_sha="$("$GIT_BIN" -C "$EXT_DIR/HybridDynamicRT" rev-parse HEAD)"
sionna_sha="$("$GIT_BIN" -C "$EXT_DIR/sionna" rev-parse HEAD)"
radarsimpy_sha="$("$GIT_BIN" -C "$EXT_DIR/radarsimpy" rev-parse HEAD)"
raw_adc_sha="$("$GIT_BIN" -C "$EXT_DIR/Raw_ADC_radar_dataset_for_automotive_object_detection" rev-parse HEAD)"
openems_sha="$("$GIT_BIN" -C "$EXT_DIR/openEMS" rev-parse HEAD)"
csxcad_sha="$("$GIT_BIN" -C "$EXT_DIR/CSXCAD" rev-parse HEAD)"
gprmax_sha="$("$GIT_BIN" -C "$EXT_DIR/gprMax" rev-parse HEAD)"

cat > "$EXT_DIR/reference-locks.md" <<EOF
# Reference Locks

This file is updated by \`${ROOT_DIR}/scripts/fetch_references.sh\`.

## Latest

- Date: $date_str
- HybridDynamicRT: $hybrid_sha
- sionna: $sionna_sha
- radarsimpy: $radarsimpy_sha
- Raw_ADC_radar_dataset_for_automotive_object_detection: $raw_adc_sha
- openEMS: $openems_sha
- CSXCAD: $csxcad_sha
- gprMax: $gprmax_sha
EOF

echo "[done] Updated $EXT_DIR/reference-locks.md"
