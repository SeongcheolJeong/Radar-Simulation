# Frontend Runtime Purpose Presets

## Purpose

Expose two practical implementation tracks in the frontend so operators can choose by purpose instead of manually rebuilding backend/runtime fields every time:

- low-fidelity path: `RadarSimPy + FFD`
- high-fidelity path: `ray-tracing backend`

## Presets

The runtime panel now exposes three preset buttons:

- `Low Fidelity: RadarSimPy + FFD`
  - backend: `radarsimpy_rt`
  - runtime provider: `avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths`
  - required modules: `radarsimpy`
  - simulation mode: `radarsimpy_adc`
  - device hint: `cpu`
- `High Fidelity: Sionna-style RT`
  - backend: `sionna_rt`
  - runtime provider: `avxsim.runtime_providers.mitsuba_rt_provider:generate_sionna_like_paths_from_mitsuba`
  - required modules: `mitsuba,drjit`
  - simulation mode: `auto`
  - device hint: `gpu`
  - advanced sample: fills `ego_origin_m`, `chirp_interval_s`, `min_range_m`, and a non-empty `spheres` JSON array
- `High Fidelity: PO-SBR`
  - backend: `po_sbr_rt`
  - runtime provider: `avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr`
  - required modules: `rtxpy,igl`
  - simulation mode: `auto`
  - device hint: `gpu`
  - advanced sample: fills repo/geometry defaults plus `bounces`, `rays_per_lambda`, angle defaults, and optional `components` JSON

## FFD Inputs

The runtime panel now accepts:

- `TX FFD Files (comma/newline)`
- `RX FFD Files (comma/newline)`

These are emitted into `scene_overrides.backend.tx_ffd_files` and `scene_overrides.backend.rx_ffd_files`.

## Advanced Controls

The runtime panel now exposes provider-specific advanced sections when the selected backend/provider matches:

- `Sionna-style RT Advanced`
  - `Mitsuba Ego Origin`
  - `Mitsuba Chirp Interval`
  - `Mitsuba Min Range`
  - `Mitsuba Spheres JSON`
- `PO-SBR Advanced`
  - `PO-SBR Repo Root`
  - `PO-SBR Geometry Path`
  - chirp/bounce/rays and angle controls
  - `PO-SBR Components JSON`

The purpose preset buttons also load sample values for these sections so a user does not start from an invalid empty runtime payload.

## Runtime Diagnostics

The runtime panel now exposes a `Runtime Diagnostics` surface with:

- availability badges such as `state:*`, `modules:*`, `sim:*`, `adc:*`, `license:*`
- a compact multiline summary showing:
  - backend/provider
  - runtime mode
  - module report
  - license source
  - simulation usage / ADC source
  - runtime error when present

This is fed from the actual `graph_run_summary` metadata when a run exists, and falls back to planned runtime configuration when the user has not run yet.

## Compare Workflow

The Decision Pane now exposes a lightweight operator workflow for low-vs-high track comparison:

- `Use Current as Compare`
  - locks the current run as the compare reference
  - keeps that reference pinned while the operator switches runtime presets and runs again
- `Run Preset Pair Compare`
  - executes any selected `baseline_preset -> target_preset` pair
  - default is `low_fidelity_radarsimpy_ffd -> current_config`
  - when `target_preset` is not `current_config`, the frontend also applies that preset into the runtime panel so the visible controls match the executed target run
- `Run Low -> Current Compare`
  - executes a low-fidelity `radarsimpy_rt` baseline first
  - then runs the current frontend track and pins the low-fidelity result as compare input
  - this is now a convenience wrapper over the generic preset-pair runner
  - reports `blocked` when the low-fidelity runtime is unavailable, instead of leaving the UI in an ambiguous state
- `Track Compare Workflow`
  - shows current/compare track labels
  - keeps the recommended sequence visible inside the UI

Practical flow:

1. Run the first track.
2. Click `Use Current as Compare`.
3. Switch to the other runtime preset.
4. Run again.
5. Inspect `Artifact Inspector` diff and use `Policy Gate` / `Run Session`.

Fast path:

1. Configure the target high-fidelity track.
2. Click `Run Preset Pair Compare` and keep `baseline_preset=low_fidelity_radarsimpy_ffd`.
3. Set `target_preset=current_config` to use the current runtime panel as-is, or select a concrete preset to force the target track.
4. If the low-fidelity runtime is installed, inspect the generated compare pair immediately.
5. If the UI reports `track_compare_runner_blocked`, install or expose the `radarsimpy` runtime first.

Shortcut:

1. Configure the target high-fidelity track manually.
2. Click `Run Low -> Current Compare`.
3. If the low-fidelity runtime is installed, inspect the generated compare pair immediately.
4. If the UI reports `track_compare_runner_blocked`, install or expose the `radarsimpy` runtime first.

The Decision Pane also keeps a dedicated `track_compare_status` line so compare-runner state is preserved even after later `Policy Gate`, `Run Session`, or `Export Session` actions update the general decision status.

The `Artifact Inspector` now also classifies the current-vs-compare pair into:

- `aligned`
- `review`
- `hold`

using concrete evidence from:

- ADC/RD/RA shape equality
- path-count delta
- top RD/RA peak-bin drift
- ADC source changes
- required/optional artifact presence deltas

## Backend Behavior

Path-based backends now share the same antenna-aware FMCW synth path:

- `analytic_targets`
- `mesh_material_stub`
- `sionna_rt`
- `po_sbr_rt`
- `radarsimpy_rt`

When `tx_ffd_files/rx_ffd_files` are present, the synth path loads `FfdAntennaModel` and applies antenna gain during ADC construction.

## RadarSimPy Limitation

`radarsimpy_rt` can return a runtime ADC payload via `sim_radar`, but that payload does not currently ingest repo-side `.ffd` files directly.

Current rule:

- no FFD: use runtime ADC payload when available
- FFD enabled: use runtime/provider paths + repo synth with `FfdAntennaModel`

This keeps the low-fidelity RadarSimPy flow usable while still letting the operator inject measured antenna patterns.

## Local Runtime Bootstrap

The repo now auto-discovers a local RadarSimPy runtime for frontend/API workflows when available:

- package roots:
  - `RADARSIMPY_PACKAGE_ROOT`
  - bundled trial package under `external/radarsimpy_trial/...`
  - repo source tree under `external/radarsimpy/src`
- libcompat:
  - `RADARSIMPY_LIBCOMPAT_DIR`
  - bundled `external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu`
- license:
  - existing `RADARSIMPY_LICENSE_FILE`
  - staged/import-time license under the runtime package
  - repo-local `external/radarsimpy/src/radarsimpy/license_RadarSimPy_*.lic`

This is what allows `Run Low -> Current Compare` and the default `Run Preset Pair Compare` flow to reach `ready` in the local workspace without manually exporting shell paths first.

## Decision Brief

`Export Brief` now includes a `Runtime Compare` section with:

- current/compare track labels
- stored compare-runner status
- current runtime diagnostics block
- compare runtime diagnostics block

It also includes a `Compare Assessment` block with:

- compare assessment status
- compare flags
- shape/path/peak delta evidence
- ADC source delta
- required artifact coverage and artifact presence delta

## Current Scope

This repo does not currently contain a direct `OptiX` or `HybridDynamicRT` runtime backend.

Today the practical high-fidelity choices exposed in the frontend are:

- `sionna_rt` through the repo's Mitsuba-based provider
- `po_sbr_rt` through the PO-SBR runtime provider
