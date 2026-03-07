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
  - required modules: `mitsuba`
  - simulation mode: `auto`
  - device hint: `gpu`
- `High Fidelity: PO-SBR`
  - backend: `po_sbr_rt`
  - runtime provider: `avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr`
  - simulation mode: `auto`
  - device hint: `gpu`

## FFD Inputs

The runtime panel now accepts:

- `TX FFD Files (comma/newline)`
- `RX FFD Files (comma/newline)`

These are emitted into `scene_overrides.backend.tx_ffd_files` and `scene_overrides.backend.rx_ffd_files`.

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

## Current Scope

This repo does not currently contain a direct `OptiX` or `HybridDynamicRT` runtime backend.

Today the practical high-fidelity choices exposed in the frontend are:

- `sionna_rt` through the repo's Mitsuba-based provider
- `po_sbr_rt` through the PO-SBR runtime provider
