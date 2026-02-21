# Native Scene Path Generator Contract (M11.2)

## Goal

Introduce a non-frame backend interface for object scene input that directly emits canonical paths and ADC without Hybrid frame folders.

## Backend Type

- `backend.type = analytic_targets`

This backend uses analytic point-target kinematics to generate `paths_by_chirp`:

- range evolution: `r(k) = r0 + v * k * chirp_interval_s`
- delay: `tau = 2r/c`
- Doppler: `fd = 2v/lambda`
- direction: from `az_deg`, `el_deg`

## Required Input (`analytic_targets`)

Backend keys:

- `n_chirps`
- `tx_pos_m` (shape `n_tx x 3`)
- `rx_pos_m` (shape `n_rx x 3`)
- `targets` (non-empty list)

Target keys:

- `range_m`
- optional: `radial_velocity_mps`, `az_deg`, `el_deg`, `amp`, `range_amp_exponent`

Radar keys:

- `fc_hz`
- `slope_hz_per_s`
- `fs_hz`
- `samples_per_chirp`

## Entry Point

- `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/scene_pipeline.py`
  - `run_object_scene_to_radar_map(...)`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_analytic_backend.py
```

## Limits

- This is interface scaffolding and deterministic stub, not full RT physics.
- Multipath/material reflection orders are out of scope for M11.2 and targeted in M11.3+.
