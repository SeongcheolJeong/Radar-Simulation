# Sionna RT Backend Adapter Contract (M13.1)

## Goal

Add a native scene backend that consumes Sionna-exported path payloads and emits canonical artifacts:

1. `path_list.json`
2. `adc_cube.npz`
3. `radar_map.npz`

## Backend Type

- `backend.type = sionna_rt`

Required keys:

- `n_chirps`
- `tx_pos_m`
- `rx_pos_m`
- one of:
  - `sionna_paths_json` (JSON file path)
  - `paths_payload` (inline JSON object)

`sionna_paths_json` / `paths_payload` accepted forms:

1. `paths_by_chirp`:
   - list length = `n_chirps`
2. `paths`:
   - flat list with per-path `chirp_idx` or `chirp_index`

Per-path canonical fields:

- `delay_s`
- `doppler_hz` (or `fd_hz`)
- `unit_direction` or `u` (`[ux,uy,uz]`)
- `amp` / `amp_complex` / `complex_gain`
- optional `path_id`, `material_tag`, `reflection_order`, `pol_matrix`

## Code Paths

- adapter:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/adapters/sionna_rt_paths.py`
- scene backend routing:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/scene_pipeline.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_sionna_backend.py
```

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_backend_parity_sionna_rt.py
```

## Acceptance

M13.1 is accepted only if:

1. `sionna_rt` backend emits canonical outputs
2. parity harness confirms map parity against analytic reference on a matched synthetic scene
