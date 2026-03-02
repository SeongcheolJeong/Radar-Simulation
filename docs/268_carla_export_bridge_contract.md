# CARLA Export Bridge Contract (M18.33)

## Goal

Integrate CARLA scene-export payloads into the existing object-scene ingestion path without changing downstream radar contracts.

Pipeline:

1. `carla_export.json` (actors + sensor mount)
2. CARLA parser normalization -> `asset_manifest.json`
3. bridge conversion -> `scene.json` (`backend.type=mesh_material_stub`)
4. run scene pipeline -> canonical artifacts:
   - `path_list.json`
   - `adc_cube.npz`
   - `radar_map.npz`

## Core CLIs

```bash
PYTHONPATH=src python3 scripts/build_asset_manifest_from_carla_export.py \
  --carla-export-json /path/to/carla_export.json \
  --output-asset-manifest-json /path/to/asset_manifest.json \
  --strict
```

```bash
PYTHONPATH=src python3 scripts/build_mesh_scene_from_carla_export.py \
  --carla-export-json /path/to/carla_export.json \
  --output-asset-manifest-json /path/to/asset_manifest.json \
  --output-scene-json /path/to/scene.json \
  --strict
```

## Input Expectations

- top-level required:
  - `sensor_mount` (`tx_pos_m`, `rx_pos_m`, optional `ego_pos_m`)
  - `actors` (list)
- top-level optional:
  - `scene_id`, `simulation_defaults`, `radar`, `materials`, `map_config`
  - `schema_profile` (`carla_export_v1`), `schema_version` (`1`)
- actor fields:
  - id: `actor_id` or `id`
  - type: `actor_type` or `type`
  - position: `centroid_m` or `location_m` or `position_m`
  - velocity: `velocity_mps` / `velocity_world_mps` / `velocity`
    or (`speed_mps` + `forward_m`) or `radial_velocity_mps`
  - optional: `material_tag`, `mesh_area_m2`, `bbox_extent_m`, `rcs_scale`, `reflection_order`

## Output Guarantees

- normalized `asset_manifest` with:
  - `objects[*].source_carla_actor_id`
  - `objects[*].source_carla_actor_type`
  - `objects[*].mesh_area_m2` (auto-estimated from bbox when missing)
- parser metadata includes:
  - actor/object counts
  - excluded actor counts (ego/sensor/filter)
  - actor type counts
  - auto mesh-area derivation counts

## Filtering Rules

- sensor actors (`actor_type` starts with `sensor.`) are excluded by default
- ego actor is excluded by default (`--include-ego-actor` can override)
- optional exact-type allow/deny filters:
  - `--include-actor-types`
  - `--exclude-actor-types`

## Validation

```bash
PYTHONPATH=src python3 scripts/validate_carla_export_bridge.py
```
