# Mesh Scene Import Bridge Contract (M12.1)

## Goal

Bridge external scene asset manifests into runnable object-scene JSON for `mesh_material_stub`.

Pipeline:

1. external `asset_manifest.json`
2. bridge conversion
3. output `scene.json` (`backend.type=mesh_material_stub`)
4. run object-scene pipeline

## Core CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_mesh_scene_from_asset_manifest.py \
  --asset-manifest-json /path/to/asset_manifest.json \
  --output-scene-json /path/to/scene_from_asset.json
```

## Input Manifest Schema (Bridge)

Required keys:

- `sensor_mount`
  - `tx_pos_m`
  - `rx_pos_m`
- `objects` (non-empty)

Optional keys:

- `scene_id`
- `simulation_defaults`
- `radar`
- `materials` (map or list)

Object aliases supported:

- `object_id` or `id`
- `centroid_m` or `bbox_center_m`
- `material_tag` or `material`
- `mesh_area_m2` or `mesh_area`

## Output Scene Guarantees

- `backend.type = mesh_material_stub`
- normalized `objects` + `materials` fields
- radar defaults present (`fc_hz`, `slope_hz_per_s`, `fs_hz`, `samples_per_chirp`)
- optional `asset_bridge_metadata`

## Code Paths

- Bridge module:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/scene_asset_bridge.py`
- Bridge CLI:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_mesh_scene_from_asset_manifest.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mesh_scene_import_bridge.py
```
