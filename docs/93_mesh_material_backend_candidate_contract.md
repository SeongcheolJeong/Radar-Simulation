# Mesh/Material Backend Candidate Contract (M12.0)

## Goal

Define and implement the first mesh/material-aware scene backend candidate that maps object/material scene inputs to canonical outputs.

Backend type:

- `backend.type = mesh_material_stub`

## Input Schema (Candidate)

Required backend keys:

- `n_chirps`
- `tx_pos_m` (`n_tx x 3`)
- `rx_pos_m` (`n_rx x 3`)
- `objects` (non-empty list)

Required object keys:

- `object_id`
- `centroid_m` (`[x,y,z]`)

Optional backend keys:

- `chirp_interval_s`
- `ego_pos_m`
- `materials` map (`material_tag -> {reflectivity, attenuation_db}`)
- `range_amp_exponent`
- `noise_sigma`

Optional object keys:

- `velocity_mps` (`[vx,vy,vz]`) or `radial_velocity_mps`
- `material_tag`
- `amp`
- `rcs_scale`
- `mesh_area_m2`
- `reflection_order`
- `path_id`

## Path Synthesis Rule (Candidate Physics)

For each object and chirp:

1. update object position with velocity model
2. derive range/direction from `ego_pos_m`
3. compute Doppler from radial velocity
4. compute amplitude with:
   - material reflectivity/loss
   - object `rcs_scale`, `mesh_area_m2`
   - range power-law

This is a deterministic candidate backend (not full RT).

## Output Guarantees

- canonical `path_list.json`, `adc_cube.npz`, `radar_map.npz`
- path metadata includes:
  - `path_id`
  - `material_tag`
  - `reflection_order`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_mesh_material_backend.py
```
