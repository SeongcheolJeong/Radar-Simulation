# PO-SBR Backend Adapter Contract (M13.2)

## Goal

Add a candidate backend that consumes PO-SBR-style exported paths and emits canonical outputs:

1. `path_list.json`
2. `adc_cube.npz`
3. `radar_map.npz`

## Backend Type

- `backend.type = po_sbr_rt`

Required keys:

- `n_chirps`
- `tx_pos_m`
- `rx_pos_m`
- one of:
  - `po_sbr_paths_json`
  - `paths_payload`
  - `runtime_provider` (`module:function`, direct runtime coupling path)

`po_sbr_paths_json` / `paths_payload` accepted forms:

1. `paths_by_chirp` list
2. flat `paths` list with chirp index fields (`chirp_idx`/`chirp_index`)

Supported per-path forms:

- delay:
  - `delay_s`, or
  - `range_m` + `range_mode(one_way|round_trip)`
- Doppler:
  - `doppler_hz`/`fd_hz`, or
  - `radial_velocity_mps` (converted using `fc_hz`)
- direction:
  - `unit_direction`/`u`, or
  - `az/el` (deg or rad)
- amplitude:
  - `amp`, `amp_complex`, `complex_gain`, or
  - PO-SBR proxy tuple (`rcs_dbsm`, `path_loss_db`, `bounce_loss_db`, `phase_rad`)

## Runtime Coupling Note

`po_sbr_rt` backend supports direct runtime coupling via `runtime_provider` (M14.0+).
Detailed runtime/fallback policy contract is documented in:

- `/Users/seongcheoljeong/Documents/Codex_test/docs/105_scene_runtime_coupling_contract.md`

## Code Paths

- adapter:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/adapters/po_sbr_paths.py`
- backend routing:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/scene_pipeline.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_po_sbr_backend.py
```

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_backend_parity_po_sbr_rt.py
```

## Acceptance

M13.2 is accepted only if:

1. `po_sbr_rt` backend emits canonical outputs from PO-SBR path payloads
2. parity harness passes on matched analytic vs PO-SBR synthetic scenario
