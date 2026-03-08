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

Quick meaning:

- `manual=explanation`
- `generated=evidence`
- `baseline=reference-only`

If you want explanation, read:

- [Documentation Index](../README.md)
- [Project Structure And User Manual](../282_project_structure_and_user_manual.md)

If you want evidence, read from this folder.

If you want a frontend-specific evidence routing page first, read:

- [Frontend Evidence Map](../332_frontend_evidence_map.md)
- [Frontend Evidence 맵](../333_frontend_evidence_map_ko.md)

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
| Graph Lab high-fidelity runtime timing | `graph_lab_high_fidelity_runtime_timing_latest.json` | current frontend/API timing verdict for Sionna-style RT vs PO-SBR |
| frontend runtime payload contract | `frontend_runtime_payload_provider_info_optional_latest.json` | current optional/runtime contract summary |
| paid RadarSimPy frontend/runtime contract | `frontend_runtime_payload_provider_info_paid_6m.json` | paid runtime-oriented frontend payload evidence |
| Sionna-style RT parity evidence | `scene_backend_parity_sionna_rt_latest.json` | current analytic-vs-sionna parity summary |
| PO-SBR parity evidence | `scene_backend_parity_po_sbr_rt_latest.json` | current analytic-vs-PO-SBR parity summary |
| release-candidate subset closure | `canonical_release_candidate_subset_latest.json` | current cross-track subset execution summary |
| latest RadarSimPy overall status | `radarsimpy_final_status_latest.json` | single status-style entry point for RadarSimPy work |

## By Role From docs/

| If you came here as... | Start with this checklist | Then open | If you need explanation, return to... |
| --- | --- | --- | --- |
| Operator | [Frontend Evidence Checklist](#frontend-evidence-checklist) | `graph_lab_playwright_snapshots/latest/decision_brief.md` | [Operator](../README.md#role-operator) |
| Classic Dashboard User | [Frontend Evidence Checklist](#frontend-evidence-checklist) | `frontend_quickstart_v1.json` | [Classic Dashboard User](../README.md#role-classic-dashboard-user) |
| Developer | [Frontend Evidence Checklist](#frontend-evidence-checklist), [RadarSimPy Evidence Checklist](#radarsimpy-evidence-checklist), or [PO-SBR Evidence Checklist](#po-sbr-evidence-checklist) | the checklist that matches the subsystem you changed | [Developer](../README.md#role-developer) |
| Validator | [RadarSimPy Evidence Checklist](#radarsimpy-evidence-checklist) or [PO-SBR Evidence Checklist](#po-sbr-evidence-checklist) | the subsystem-specific `_latest` or dated report | [Validator](../README.md#role-validator) |
| Paid RadarSimPy Validator | [RadarSimPy Evidence Checklist](#radarsimpy-evidence-checklist) | `radarsimpy_production_release_gate_latest.json` | [Paid RadarSimPy Validator](../README.md#role-paid-radarsimpy-validator) |

## Current Evidence Checklists

Use each checklist in this order:

1. Open the stable/current evidence files.
2. Check `Healthy if:` and `Usually unhealthy because:`.
3. Run `Fastest first check:` if the current state is unclear or failing.
4. Run `Escalate with:` if the quick check is not enough.
5. Re-open `Expect refreshed evidence:` and compare the refreshed files.
6. If still blocked, follow `If this checklist fails, open next:`.

<a id="frontend-evidence-checklist"></a>

### Frontend

Need explanation first:

- [Frontend Runtime Purpose Presets](../280_frontend_runtime_purpose_presets.md)
- [Frontend Dashboard Usage](../116_frontend_dashboard_usage.md)
- [Project Structure And User Manual](../282_project_structure_and_user_manual.md)

Open these first:

1. `graph_lab_playwright_e2e_latest.json`
2. `graph_lab_playwright_snapshots/latest/`
3. `graph_lab_high_fidelity_runtime_timing_latest.json`
4. `frontend_runtime_payload_provider_info_optional_latest.json`
5. `frontend_quickstart_v1.json`

You should be able to answer:

- does the current browser E2E pass
- do the latest screenshots and decision brief look correct
- is the current interactive high-fidelity path still `Sionna-style RT` and not `PO-SBR`
- does the frontend/runtime payload contract still match the backend
- does the quick demo path still produce a usable summary

Healthy if:

- `graph_lab_playwright_e2e_latest.json` shows a passing current browser run
- `graph_lab_playwright_snapshots/latest/` reflects the current UI and exported decision brief
- `graph_lab_high_fidelity_runtime_timing_latest.json` shows `high_fidelity_sionna_rt` as completed within budget and keeps `PO-SBR` out of the interactive-ready path unless that release story changes
- `frontend_runtime_payload_provider_info_optional_latest.json` stays consistent with the current backend/runtime contract
- `frontend_quickstart_v1.json` still represents a usable demo/API path

Usually unhealthy because:

- the browser E2E regressed even though the API is still alive, which usually points at Graph Lab UI flow drift
- the high-fidelity timing report no longer matches the release story, which usually points at runtime-environment drift or frontend preset changes
- the frontend/runtime payload report no longer matches expectations, which usually points at backend contract or override-builder changes
- the quick demo summary no longer looks usable, which usually points at local server bootstrap or demo-route wiring problems

Fastest first check:

- `PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py`

Escalate with:

- `PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers PYTHONPATH=src .venv/bin/python scripts/validate_graph_lab_playwright_e2e.py --require-playwright --output-json docs/reports/graph_lab_playwright_e2e_latest.json`

If this checklist fails, open next:

- `graph_lab_playwright_snapshots/latest/decision_brief.md`
- `graph_lab_playwright_snapshots/latest/`
- `graph_lab_high_fidelity_runtime_timing_latest.json`
- `frontend_runtime_payload_provider_info_optional_latest.json`

Reproduce with:

- `PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py`
- `PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers PYTHONPATH=src .venv/bin/python scripts/validate_graph_lab_playwright_e2e.py --require-playwright --output-json docs/reports/graph_lab_playwright_e2e_latest.json`
- `PYTHONPATH=src .venv/bin/python scripts/run_graph_lab_high_fidelity_runtime_timing.py --api-base http://127.0.0.1:8101 --output-json docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json`
- `PY_BIN=.venv/bin/python scripts/run_graph_lab_local.sh 8081 8101`
- `PY_BIN=.venv/bin/python scripts/run_web_e2e_dashboard_local.sh 8080 8099`

Expect refreshed evidence:

- `graph_lab_playwright_e2e_latest.json`
- `graph_lab_playwright_snapshots/latest/`
- `graph_lab_high_fidelity_runtime_timing_latest.json`
- `frontend_quickstart_v1.json`

Escalate to role:

- [Operator](../README.md#role-operator)
- [Classic Dashboard User](../README.md#role-classic-dashboard-user)
- [Developer](../README.md#role-developer)

<a id="radarsimpy-evidence-checklist"></a>

### RadarSimPy

Need explanation first:

- [RadarSimPy Runtime](../285_install_radarsimpy_runtime.md)
- [Validation Checkpoints](../04_validation_checkpoints.md)
- [Scene Backend Golden Path Contract](../251_scene_backend_golden_path_contract.md)

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

Healthy if:

- `radarsimpy_final_status_latest.json` is green overall
- `radarsimpy_production_release_gate_latest.json` is ready/pass
- `radarsimpy_readiness_checkpoint_latest.json` is ready/pass
- wrapper integration and integration smoke reports both stay passing

Usually unhealthy because:

- production gate or readiness no longer reports ready/pass, which usually points at runtime availability, license access, or environment drift
- wrapper integration fails while final status was previously green, which usually points at coupling or provider-contract regressions
- smoke gate fails after wrapper integration passes, which usually points at runtime execution drift rather than pure wiring

Fastest first check:

- `PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_wrapper_integration_gate.py --output-summary-json docs/reports/radarsimpy_wrapper_integration_gate_manual.json`

Escalate with:

- `PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_integration_smoke_gate.py --output-summary-json docs/reports/radarsimpy_integration_smoke_gate_manual.json`
- `PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_paid_6m_gate_ci.sh`

If this checklist fails, open next:

- `radarsimpy_production_release_gate_latest.json`
- `radarsimpy_readiness_checkpoint_latest.json`
- `radarsimpy_wrapper_integration_gate_production_latest.json`
- `radarsimpy_integration_smoke_gate_production_latest.json`

Reproduce with:

- `PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_wrapper_integration_gate.py --output-summary-json docs/reports/radarsimpy_wrapper_integration_gate_manual.json`
- `PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_integration_smoke_gate.py --output-summary-json docs/reports/radarsimpy_integration_smoke_gate_manual.json`
- `PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_paid_6m_gate_ci.sh`

Expect refreshed evidence:

- `radarsimpy_wrapper_integration_gate_manual.json`
- `radarsimpy_integration_smoke_gate_manual.json`
- `radarsimpy_production_release_gate_paid_6m.json`
- `radarsimpy_readiness_checkpoint_paid_6m.json`
- `radarsimpy_simulator_reference_parity_paid_6m.json`

Escalate to role:

- [Developer](../README.md#role-developer)
- [Validator](../README.md#role-validator)
- [Paid RadarSimPy Validator](../README.md#role-paid-radarsimpy-validator)

<a id="po-sbr-evidence-checklist"></a>

### PO-SBR

Need explanation first:

- [PO-SBR Runtime](../287_install_po_sbr_runtime.md)
- [Validation Checkpoints](../04_validation_checkpoints.md)
- [PO-SBR Backend Contract](../103_po_sbr_backend_contract.md)

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

Healthy if:

- the post-change gate is ready/pass
- the progress snapshot shows required checkpoints ready
- the operator handoff closure remains complete
- local-ready regression and baseline drift stay within the accepted envelope

Usually unhealthy because:

- the strict post-change gate stopped passing, which usually points at runtime-affecting contract drift
- the progress snapshot no longer shows required checkpoints ready, which usually means the closure set is incomplete
- local-ready regression or baseline drift moved out of envelope, which usually indicates physical-output or acceptance-threshold drift

Fastest first check:

- `PYTHONPATH=src .venv/bin/python scripts/run_po_sbr_post_change_gate.py --strict`

Escalate with:

- `PYTHONPATH=src .venv/bin/python scripts/show_po_sbr_progress.py --strict-ready --output-json docs/reports/po_sbr_progress_snapshot_manual.json`

If this checklist fails, open next:

- `po_sbr_progress_snapshot_2026_03_02.json`
- `po_sbr_operator_handoff_closure_2026_03_01.json`
- `po_sbr_local_ready_regression_2026_03_01_pc_self.json`
- `po_sbr_local_ready_baseline_drift_2026_03_01_pc_self.json`

Reproduce with:

- `PYTHONPATH=src .venv/bin/python scripts/run_po_sbr_post_change_gate.py --strict`

Expect refreshed evidence:

- `po_sbr_post_change_gate_*.json`
- `po_sbr_progress_snapshot_manual.json`

Escalate to role:

- [Developer](../README.md#role-developer)
- [Validator](../README.md#role-validator)

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
- `scene_backend_parity_po_sbr_rt_*`

### High-Fidelity Backend Parity

- `scene_backend_parity_sionna_rt_*`
- `scene_backend_parity_po_sbr_rt_*`

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
