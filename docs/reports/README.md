# Generated Reports Index

## Purpose

This directory stores generated outputs, validation summaries, gate results, release bundles, and visual-regression artifacts.

Unlike the static documents in `docs/`, most files here are machine-generated and time-stamped.

Use this page to find the right report instead of opening old JSON files at random.

## Static Docs vs Generated Reports

- static docs
  - live in `docs/`
  - explain architecture, setup, usage, contracts, and workflows
- generated reports
  - live in `docs/reports/`
  - are outputs from validators, gates, demos, runtime runs, and release scripts

If you want explanation, read:

- [Documentation Index](../README.md)
- [Project Structure And User Manual](../282_project_structure_and_user_manual.md)

If you want evidence, read from this folder.

## Start Here

Most useful stable entry points:

- `frontend_quickstart_v1.json`
  - quick frontend/demo summary
- `graph_lab_playwright_e2e_latest.json`
  - latest Graph Lab browser E2E summary
- `radarsimpy_final_status_latest.json`
  - latest RadarSimPy status summary
- `graph_lab_playwright_snapshots/latest/`
  - latest UI screenshots and exported decision brief

Related snapshot guide:

- [Graph Lab Playwright Snapshots](graph_lab_playwright_snapshots/README.md)

## Common Report Families

### Frontend

- `frontend_quickstart_v1.json`
- `frontend_runtime_payload_provider_info_optional_latest.json`
- `frontend_runtime_payload_provider_info_paid_6m.json`
- `graph_lab_playwright_e2e_latest.json`
- `graph_lab_playwright_snapshots/latest/`

### RadarSimPy

- `radarsimpy_final_status_latest.json`
- `radarsimpy_*`
- `radarsimpy_production_release_gate_*`
- `radarsimpy_readiness_checkpoint_*`
- `radarsimpy_simulator_reference_parity_*`

### PO-SBR

- `po_sbr_post_change_gate_*`
- `po_sbr_progress_snapshot_*`
- `po_sbr_local_ready_*`
- `po_sbr_physical_full_track_*`
- `po_sbr_operator_handoff_closure_*`

### Integration And Campaign Runs

- `integration_full_*`
- `avx_export_benchmark_*`
- `public_scene_asset_onboarding_*`
- `path_power_*`
- `measured_replay_*`

## Naming Guidance

In general:

- prefer files ending with `_latest.json` when they exist
- prefer directories named `latest/` when they exist
- treat dated files as historical records unless you specifically need that run

Examples:

- use `graph_lab_playwright_e2e_latest.json`
  - not an older dated E2E output
- use `graph_lab_playwright_snapshots/latest/`
  - not `baseline/` unless you are maintaining visual regression

## Important Subdirectories

- `graph_lab_playwright_snapshots/`
  - screenshot baselines and latest captures
- `baselines/`
  - saved comparison baselines
- `integration_full_*/`
  - large integration campaign outputs
- `radarsimpy_runtime_pilot_wrapper_gate_*/`
  - RadarSimPy pilot gate outputs with pipeline artifacts

## Operator Recommendation

If you are debugging or reviewing a current result:

1. open the corresponding static doc in `docs/`
2. open the stable latest report from this folder
3. open the dated historical file only if you need drift or regression history

That order prevents reading stale artifacts as if they were current status.
