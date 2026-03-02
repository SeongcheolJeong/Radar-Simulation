# RadarSimPy API Coverage (Excluding `sim_lidar`)

## Scope

- Source API index: `https://radarsimx.github.io/radarsimpy/api/index.html`
- API index version baseline: `15.0.1`
- Integration policy: expose the full API index surface **except** `sim_lidar()`.

## Wrapper Module

- Module: `src/avxsim/radarsimpy_api.py`
- Exported at package root: `src/avxsim/__init__.py`
- Runtime provider integration: `src/avxsim/runtime_providers/radarsimpy_rt_provider.py`
  now routes RadarSimPy object/simulation calls through this wrapper.

## Covered APIs

### Radar Model

- `Transmitter`
- `Receiver`
- `Radar`

### Simulator

- `sim_radar`
- `sim_rcs`

### Processing

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

### Tools

- `roc_pd`
- `roc_snr`

## Explicit Exclusion

- `sim_lidar`

## Validation

- Script: `scripts/run_radarsimpy_wrapper_integration_gate.py`
- Purpose:
  - Runs the integrated RadarSimPy wrapper gate in one command.
  - Optionally adds strict real-runtime checks with `--with-real-runtime`.
- Script: `scripts/validate_radarsimpy_api_coverage_excluding_sim_lidar.py`
- Checks:
  - API coverage completeness against the integration contract.
  - Wrapper dispatch for each covered API symbol.
  - `sim_lidar` absence from supported exports.
- Script: `scripts/validate_radarsimpy_wrapper_entrypoint_guard.py`
- Checks:
  - No direct `radarsimpy` imports in `src/avxsim`/`scripts` outside
    the wrapper entrypoint (`src/avxsim/radarsimpy_api.py`).
- Script: `scripts/validate_run_radarsimpy_wrapper_integration_gate.py`
- Checks:
  - Gate runner executes successfully and includes required checks.
