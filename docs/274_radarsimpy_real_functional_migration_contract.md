# RadarSimPy Real Functional Migration Contract

## Goal
Move `radarsimpy_rt` from import-check + analytic placeholder behavior to real functional runtime simulation using `radarsimpy.sim_radar` while preserving existing pipeline outputs (`path_list.json`, `adc_cube.npz`, `radar_map.npz`).

## Implemented Behavior

### Runtime Provider (`radarsimpy_rt_provider`)
- File: `src/avxsim/runtime_providers/radarsimpy_rt_provider.py`
- `generate_radarsimpy_like_paths` now supports:
  - `simulation_mode=analytic_paths`: old analytic path generation only.
  - `simulation_mode=radarsimpy_adc`: strict real simulation path (uses `Radar`, `Transmitter`, `Receiver`, `sim_radar`).
  - `simulation_mode=auto`: try real simulation first, with optional analytic fallback only when explicitly enabled.
- Provider returns:
  - `paths_by_chirp` (canonical path payload for contract continuity)
  - optional `adc_sctr` (`[sample, chirp, tx, rx]`) when real simulation is used
  - `provider_runtime_info` metadata including `simulation_used`, shapes, and device

### Scene Pipeline (`radarsimpy_rt` backend)
- File: `src/avxsim/scene_pipeline.py`
- `_run_backend_radarsimpy_rt` now:
  - accepts optional `adc_sctr` from runtime payload
  - uses real ADC directly when compensation is not enabled (`adc_source=runtime_payload_adc_sctr`)
  - falls back to synthesized ADC from paths when direct ADC is absent or compensation is enabled
  - propagates `provider_runtime_info` into `runtime_resolution` metadata

## Trial vs Standard License

### Trial Limitation (observed)
- Trial/free tier enforces **1 TX channel** and **1 RX channel**.
- 2x4 geometry raises runtime errors from RadarSimPy.

### Standard/Production
- Multi-channel TX/RX is expected to work with proper license tier.
- The migrated provider/backend path is ready for multi-channel configurations.

## Operational Scripts

### Real runtime pilot
- File: `scripts/run_scene_runtime_radarsimpy_pilot.py`
- Added controls:
  - `--simulation-mode`
  - `--runtime-device`
  - `--fallback-to-analytic-on-error`
  - `--trial-free-tier-geometry`
  - `--require-real-simulation`

### Stepwise migration comparison
- File: `scripts/run_radarsimpy_migration_stepwise.py`
- Added controls:
  - `--radarsimpy-simulation-mode`
  - `--radarsimpy-runtime-device`
  - `--radarsimpy-fallback-to-analytic-on-error`
  - `--trial-free-tier-geometry`
  - `--require-radarsimpy-simulation-used`

## Validation
- `scripts/validate_scene_runtime_radarsimpy_provider_integration_stubbed.py`
  - covers analytic fallback compatibility
  - covers simulated ADC payload handoff (`adc_source=runtime_payload_adc_sctr`)
- `scripts/validate_run_scene_runtime_radarsimpy_pilot.py`
- `scripts/validate_run_radarsimpy_migration_stepwise.py`

## Practical Notes
- Real RadarSimPy reference and analytic/Sionna/PO-SBR candidates will not necessarily match with strict default parity thresholds.
- Use threshold overrides (`--rdra-thresholds-json`, `--adc-view-thresholds-json`) for pragmatic migration gates.
- For trial environment runs, use `--trial-free-tier-geometry` for functional execution.
