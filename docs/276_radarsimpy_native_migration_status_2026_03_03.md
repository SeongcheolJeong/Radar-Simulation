# RadarSimPy Native Migration Status (2026-03-03)

## Purpose

Integrate RadarSimPy APIs into AVx-lite so the system can run with:

- wrapper-dispatched RadarSimPy runtime calls when runtime is available
- native-core fallback implementations when runtime is missing or restricted
- policy gates that separate trial behavior from production release behavior

## Current Architecture

1. API Facade
- `src/avxsim/radarsimpy_api.py`
- Single entrypoint for RadarSimPy APIs.
- Dispatch order: upstream RadarSimPy symbol -> native core fallback.
- Applies optional license configuration from `RADARSIMPY_LICENSE_FILE`.

2. Native Core Layer
- `src/avxsim/radarsimpy_core_model.py`
- `src/avxsim/radarsimpy_core_processing.py`
- `src/avxsim/radarsimpy_core_simulator.py`
- `src/avxsim/radarsimpy_core_tools.py`
- Provides internal implementations for model/process/simulator/tools API surface.

3. Runtime Provider Integration
- `src/avxsim/runtime_providers/radarsimpy_rt_provider.py`
- `src/avxsim/scene_pipeline.py`
- Supports real RadarSimPy ADC path (`simulation_mode=radarsimpy_adc`) and fallback paths.

4. Gates and Readiness
- Wrapper gate: `scripts/run_radarsimpy_wrapper_integration_gate.py`
- Smoke gate: `scripts/run_radarsimpy_integration_smoke_gate.py`
- Readiness checkpoint: `scripts/run_radarsimpy_readiness_checkpoint.py`
- Production release gate: `scripts/run_radarsimpy_production_release_gate.py`
- Order-driven production gate runner: `scripts/run_radarsimpy_production_gate_from_order.py`
- Policy: `docs/radarsimpy_runtime_license_policy.json`

## API Coverage (excluding `sim_lidar`)

Coverage target: full API index coverage except `sim_lidar`.

- Root model/simulator:
  - `Transmitter`
  - `Receiver`
  - `Radar`
  - `sim_radar`
  - `sim_rcs`
- Processing:
  - `range_fft`
  - `doppler_fft`
  - `range_doppler_fft`
  - `cfar_ca_1d`
  - `cfar_ca_2d`
  - `cfar_os_1d`
  - `cfar_os_2d`
  - `doa_music`
  - `doa_root_music`
  - `doa_esprit`
  - `doa_iaa`
  - `doa_bartlett`
  - `doa_capon`
- Tools:
  - `roc_pd`
  - `roc_snr`

Status: implemented/exported for all supported symbols.

Evidence:
- `docs/reports/radarsimpy_function_progress_latest.json`
- `docs/reports/radarsimpy_signature_manifest_latest.json`
- `docs/reports/radarsimpy_native_parity_fixtures_latest.json`

## Real Runtime Validation Snapshot

1. Trial tier, real runtime path
- Status: ready/executed.
- Evidence:
  - `docs/reports/radarsimpy_readiness_checkpoint_real_trial_current.json`
  - `docs/reports/scene_runtime_radarsimpy_pilot_trial_real_current.json`

2. Production tier gate (no standard license)
- Status: blocked by policy/runtime constraints, not by missing wrapper/core APIs.
- Evidence:
  - `docs/reports/radarsimpy_readiness_checkpoint_real_production_current.json`
  - `docs/reports/radarsimpy_wrapper_integration_gate_production_with_trial_pkg_current.json`
  - `docs/reports/scene_runtime_radarsimpy_pilot_production_probe_current.json`

Observed production blockers:
- free-tier warning markers detected
- `license_not_activated` in production policy checks
- trial limitation in strict pilot (multi-channel TX requires standard license)

## Changes Applied In This Cycle

1. Readiness runner artifact collision fix
- `scripts/run_radarsimpy_readiness_checkpoint.py`
- Auto-generated `run_id` now uses UTC timestamp with microseconds + commit + PID.
- Prevents checkpoint artifact overwrite between repeated/concurrent runs.

2. Wrapper summary clarity
- `scripts/run_radarsimpy_wrapper_integration_gate.py`
- Summary now includes top-level `runtime_license_tier` for direct report parsing.

## Remaining Work For Production Release

1. Provide standard RadarSimPy runtime + valid `.lic` file in target runtime environment.
2. Run strict production gates with that license:
- wrapper gate with `--with-real-runtime --runtime-license-tier production --license-file ...`
- smoke gate and readiness checkpoint with same production tier/license settings.
3. Lock production evidence artifacts once all production checks pass.
