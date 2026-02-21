# Sidecar Asset Parser Contract (M12.2)

## Goal

Parse scene sidecar metadata with `glTF/OBJ` mesh references and build normalized `asset_manifest.json`.

Pipeline:

1. `scene_sidecar.json` (mesh URIs + object metadata)
2. parser normalization
3. `asset_manifest.json`
4. bridge to `mesh_material_stub` scene JSON
5. run object-scene radar pipeline

## Core CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_asset_manifest_from_sidecar.py \
  --sidecar-json /path/to/scene_sidecar.json \
  --output-asset-manifest-json /path/to/asset_manifest.json
```

## Supported Mesh Inputs

- `mesh_uri`, `mesh_file`, or `uri` per object
- mesh extensions:
  - `.gltf`, `.glb` -> `gltf`
  - `.obj` -> `obj`

Unsupported extensions are rejected.

## Output Guarantees

- normalized manifest keys: `sensor_mount`, `simulation_defaults`, `radar`, `materials`, `objects`
- objects include:
  - `source_mesh_uri`
  - `source_mesh_format` (`gltf` or `obj`)
- parser metadata:
  - `mesh_format_counts`
  - `object_count`, `material_count`

## Code Paths

- parser module:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/scene_asset_parser.py`
- parser CLI:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_asset_manifest_from_sidecar.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sidecar_asset_parser.py
```
