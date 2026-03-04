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
  - Supports `--runtime-license-tier {trial,production}` to enforce runtime
    license-tier policy in real-runtime mode.
  - Supports `--license-file` (mapped to `RADARSIMPY_LICENSE_FILE`) to activate
    licensed runtime mode when a valid `.lic` is available.
- Policy: `docs/radarsimpy_runtime_license_policy.json`
- Script: `scripts/validate_radarsimpy_runtime_license_policy.py`
- Checks:
  - Runtime license-tier boundary contract for trial vs production operation.
  - Required free-tier warning markers and production gate controls.
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
  - In `--with-real-runtime` mode, gate also enforces simulator reference parity
    under real RadarSimPy runtime environment.
- Script: `scripts/validate_radarsimpy_root_model_core_fallback.py`
- Checks:
  - Forces missing root model attrs (`Transmitter`/`Receiver`/`Radar`) and validates
    wrapper fallback to native core model implementations.
  - Confirms core model property contracts (`waveform_prop`, `txchannel_prop`,
    `bb_prop`, `rxchannel_prop`, `sample_prop`, `array_prop`, `time_prop`) and shapes.
- Script: `scripts/validate_radarsimpy_simulator_core_fallback.py`
- Checks:
  - Forces missing simulator attrs (`sim_radar`/`sim_rcs`) and validates wrapper fallback
    execution and output contracts.
  - Verifies deterministic baseband/timestamp output shape contract for `sim_radar` and
    scalar/vector result behavior for `sim_rcs`.
- Script: `scripts/validate_radarsimpy_simulator_reference_parity_optional.py`
- Checks:
  - Runs optional real-runtime parity check (auto-skip when RadarSimPy runtime is not available).
  - Supports `--require-runtime` for strict real-runtime gate enforcement (no skip allowed).
  - Supports `--output-json` to emit parity artifact (metrics/thresholds/pass/skip reason).
  - Compares native fallback `sim_radar` against reference runtime by RD peak-bin agreement and
    normalized RD-map correlation for a deterministic trial-safe point-target case.
- Script: `scripts/validate_run_radarsimpy_simulator_reference_parity_optional.py`
- Checks:
  - Validates parity artifact contract in default optional mode.
  - Validates strict runtime parity contract (`--require-runtime`) when trial runtime package is present.
- Script: `scripts/show_radarsimpy_function_progress.py`
- Purpose:
  - Prints function-level status for all supported API symbols and excluded symbols.
- Script: `scripts/validate_show_radarsimpy_function_progress.py`
- Checks:
  - Function-level progress report is `ready`.
  - All supported symbols are implemented/exported.
  - `sim_lidar` remains excluded and not exported.
- Script: `scripts/build_radarsimpy_signature_manifest.py`
- Purpose:
  - Emits a per-function signature manifest with canonical upstream signatures,
    wrapper signatures, native-core mappings, and optional runtime-reference signatures.
  - Tracks phase status:
    - `phase1_native_ready`: processing/tools native coverage.
    - `phase2_native_ready`: full supported API native coverage (root/simulator included).
- Script: `scripts/validate_build_radarsimpy_signature_manifest.py`
- Checks:
  - Manifest contract is valid.
  - Canonical signatures are defined for all supported API symbols.
  - Phase-1 native-core migration coverage is complete for processing/tools APIs.
  - Phase-2 native-core migration coverage is complete for all supported APIs.
- Script: `scripts/build_radarsimpy_native_parity_fixtures.py`
- Purpose:
  - Generates deterministic golden parity fixtures for native fallback functions
    (processing/tools + simulator APIs).
- Script: `scripts/validate_build_radarsimpy_native_parity_fixtures.py`
- Checks:
  - Fixture pack is generated successfully.
  - Wrapper fallback execution reproduces fixture outputs exactly (digest + numeric parity).
