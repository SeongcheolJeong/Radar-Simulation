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

## Current Stable Report Set

| What you need | Stable entry point | Why start here |
| --- | --- | --- |
| quick frontend/demo status | `frontend_quickstart_v1.json` | small summary for local demo/backend wiring |
| latest browser E2E status | `graph_lab_playwright_e2e_latest.json` | current Graph Lab end-to-end result |
| latest UI evidence | `graph_lab_playwright_snapshots/latest/` | screenshots and exported decision brief |
| frontend runtime payload contract | `frontend_runtime_payload_provider_info_optional_latest.json` | current optional/runtime contract summary |
| paid RadarSimPy frontend/runtime contract | `frontend_runtime_payload_provider_info_paid_6m.json` | paid runtime-oriented frontend payload evidence |
| latest RadarSimPy overall status | `radarsimpy_final_status_latest.json` | single status-style entry point for RadarSimPy work |

## Current Evidence Checklists

### Frontend

Open these first:

1. `graph_lab_playwright_e2e_latest.json`
2. `graph_lab_playwright_snapshots/latest/`
3. `frontend_runtime_payload_provider_info_optional_latest.json`
4. `frontend_quickstart_v1.json`

You should be able to answer:

- does the current browser E2E pass
- do the latest screenshots and decision brief look correct
- does the frontend/runtime payload contract still match the backend
- does the quick demo path still produce a usable summary

If this checklist fails, open next:

- `graph_lab_playwright_snapshots/latest/decision_brief.md`
- `graph_lab_playwright_snapshots/latest/`
- `frontend_runtime_payload_provider_info_optional_latest.json`

### RadarSimPy

Open these first:

1. `radarsimpy_final_status_latest.json`
2. `radarsimpy_production_release_gate_latest.json`
3. `radarsimpy_readiness_checkpoint_latest.json`
4. `radarsimpy_progress_snapshot_latest.json`
5. `radarsimpy_wrapper_integration_gate_production_latest.json`
6. `radarsimpy_integration_smoke_gate_production_latest.json`

Use these to answer:

- is the current RadarSimPy path green overall
- did production gate and readiness pass
- is the wrapper/provider integration still intact
- does the smoke gate still pass in the current environment

If this checklist fails, open next:

- `radarsimpy_production_release_gate_latest.json`
- `radarsimpy_readiness_checkpoint_latest.json`
- `radarsimpy_wrapper_integration_gate_production_latest.json`
- `radarsimpy_integration_smoke_gate_production_latest.json`

### PO-SBR

Open these first:

1. `po_sbr_post_change_gate_2026_03_02.json`
2. `po_sbr_progress_snapshot_2026_03_02.json`
3. `po_sbr_operator_handoff_closure_2026_03_01.json`
4. `po_sbr_physical_full_track_merged_checkpoint_2026_03_01.json`
5. `po_sbr_local_ready_regression_2026_03_01_pc_self.json`
6. `po_sbr_local_ready_baseline_drift_2026_03_01_pc_self.json`

Use these to answer:

- is PO-SBR currently allowed past the post-change gate
- what is the current readiness/progress state
- is the handoff/closure package complete
- did local-ready regression and baseline drift stay within the accepted envelope

If this checklist fails, open next:

- `po_sbr_progress_snapshot_2026_03_02.json`
- `po_sbr_operator_handoff_closure_2026_03_01.json`
- `po_sbr_local_ready_regression_2026_03_01_pc_self.json`
- `po_sbr_local_ready_baseline_drift_2026_03_01_pc_self.json`

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

## Latest vs Dated vs Baseline

| If you see... | Use it when... | Do not treat it as... |
| --- | --- | --- |
| `_latest.json` | you want the current stable summary | the full history of all runs |
| `latest/` | you want the current captured artifacts | the visual reference baseline |
| dated file like `*_2026_03_02.json` | you are tracing a specific run or regression point | the current default status |
| `baseline/` | you are maintaining visual regression or comparison references | the newest run result |
| `baselines/` | you need saved comparison baselines for drift analysis | the primary entry point for current status |

Practical rule:

1. open `_latest.json` first
2. open `latest/` second if you need screenshots or exported briefs
3. open dated files only for drift/history
4. open `baseline/` or `baselines/` only for reference-maintenance work

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
