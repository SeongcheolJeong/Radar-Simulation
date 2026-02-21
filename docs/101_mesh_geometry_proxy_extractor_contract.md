# Mesh Geometry Proxy Extractor Contract (M13.0)

## Goal

Auto-populate object geometry proxy fields from mesh assets when sidecar omits them:

1. `centroid_m`
2. `mesh_area_m2`

## Scope

- OBJ: vertex/face parsing based centroid + triangle area proxy
- glTF/GLB: POSITION accessor `min/max` metadata based centroid + bbox surface-area proxy

## Parser Behavior

When sidecar object omits geometry fields:

1. parser tries `infer_mesh_geometry_proxy` from mesh file
2. inferred fields are written to manifest object (`centroid_m`, `mesh_area_m2`)
3. parser metadata records auto-filled objects:
   - `auto_geometry_object_count`
   - `auto_geometry_object_ids`
   - `auto_geometry_fields`

## Code Paths

- geometry extractor:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/mesh_geometry_proxy.py`
- sidecar parser integration:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/scene_asset_parser.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mesh_geometry_proxy_extractor.py
```

## Acceptance

M13.0 is accepted only if:

1. missing geometry fields are auto-filled for both OBJ and glTF fixture cases
2. parser metadata captures auto-filled diagnostics
3. manifest remains bridge-compatible and produces canonical scene artifacts
