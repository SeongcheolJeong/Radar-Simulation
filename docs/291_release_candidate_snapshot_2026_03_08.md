# Release-Candidate Snapshot

- Date: March 8, 2026
- Scope: frontend/operator workflow, trial RadarSimPy parity, PO-SBR parity/readiness, paid RadarSimPy production closure
- Korean snapshot: [Release-Candidate Snapshot (Korean)](292_release_candidate_snapshot_2026_03_08_ko.md)
- One-page handoff: [Release Closure Handoff](294_release_closure_handoff_2026_03_08.md)
- Canonical pack: [Canonical Validation Scenario Pack](289_canonical_validation_scenario_pack.md)
- Canonical pack (Korean): [정식 검증 시나리오 팩](290_canonical_validation_scenario_pack_ko.md)
- HF-1 decision: [HF-1 Release Requirement Decision](293_hf1_release_requirement_decision_2026_03_08.md)

## Current Decision

- default release-candidate subset:
  - `FE-1`
  - `FE-2`
  - `RS-1`
  - `HF-2`
  - `RS-2`
- `HF-1` remains optional by default. See [HF-1 Release Requirement Decision](293_hf1_release_requirement_decision_2026_03_08.md).
- Include `HF-1` only when the Sionna-style RT path is explicitly in the release story for that cut.

Reason:

- the default closure path is already green end-to-end
- `HF-2` is the higher-priority high-fidelity closure path for current operator/runtime work
- `HF-1` stable evidence exists and is green, but it is not required for the current default cut

## Current Stable Outcome

The current release-candidate subset is green.

- canonical subset:
  - [canonical_release_candidate_subset_latest.json](reports/canonical_release_candidate_subset_latest.json)
  - `pass=true`
  - `step_count=8`
  - `pass_count=8`
- paid RadarSimPy production gate:
  - [radarsimpy_production_release_gate_paid_6m.json](reports/radarsimpy_production_release_gate_paid_6m.json)
  - `production_gate_status=ready`
- paid RadarSimPy readiness checkpoint:
  - [radarsimpy_readiness_checkpoint_paid_6m.json](reports/radarsimpy_readiness_checkpoint_paid_6m.json)
  - `overall_status=ready`
- PO-SBR parity:
  - [scene_backend_parity_po_sbr_rt_latest.json](reports/scene_backend_parity_po_sbr_rt_latest.json)
  - `pass=true`
- Sionna-style parity:
  - [scene_backend_parity_sionna_rt_latest.json](reports/scene_backend_parity_sionna_rt_latest.json)
  - `pass=true`
- Graph Lab browser/operator flow:
  - [graph_lab_playwright_e2e_latest.json](reports/graph_lab_playwright_e2e_latest.json)

## Stable Evidence Set

Use this set as the current release-candidate evidence bundle.

### Frontend / Operator

- [frontend_quickstart_v1.json](reports/frontend_quickstart_v1.json)
- [graph_lab_playwright_e2e_latest.json](reports/graph_lab_playwright_e2e_latest.json)
- [graph_lab_playwright_snapshots/latest/decision_brief.md](/home/seongcheoljeong/workspace/myproject/docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md)
- [graph_lab_playwright_snapshots/latest/page_full.png](/home/seongcheoljeong/workspace/myproject/docs/reports/graph_lab_playwright_snapshots/latest/page_full.png)
- [frontend_runtime_payload_provider_info_optional_latest.json](reports/frontend_runtime_payload_provider_info_optional_latest.json)

### RadarSimPy Trial / Low Fidelity

- [radarsimpy_layered_parity_suite_trial_latest.json](reports/radarsimpy_layered_parity_suite_trial_latest.json)
- [radarsimpy_layered_parity_trial_latest.json](reports/radarsimpy_layered_parity_trial_latest.json)

### High Fidelity

- [scene_backend_parity_po_sbr_rt_latest.json](reports/scene_backend_parity_po_sbr_rt_latest.json)
- [scene_backend_parity_sionna_rt_latest.json](reports/scene_backend_parity_sionna_rt_latest.json)
- latest `po_sbr_post_change_gate_*.json`
- [po_sbr_progress_snapshot_release_candidate_latest.json](reports/po_sbr_progress_snapshot_release_candidate_latest.json)

### Paid RadarSimPy Production

- [radarsimpy_production_release_gate_paid_6m.json](reports/radarsimpy_production_release_gate_paid_6m.json)
- [radarsimpy_readiness_checkpoint_paid_6m.json](reports/radarsimpy_readiness_checkpoint_paid_6m.json)
- [radarsimpy_simulator_reference_parity_paid_6m.json](reports/radarsimpy_simulator_reference_parity_paid_6m.json)
- [frontend_runtime_payload_provider_info_paid_6m.json](reports/frontend_runtime_payload_provider_info_paid_6m.json)

## How To Refresh This Snapshot

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_canonical_release_candidate_subset.py \
  --output-json docs/reports/canonical_release_candidate_subset_latest.json
```

If the release story also includes the Sionna-style RT path:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_canonical_release_candidate_subset.py \
  --with-sionna \
  --output-json docs/reports/canonical_release_candidate_subset_latest.json
```

## Pass Interpretation

Treat this snapshot as healthy when:

- canonical subset stays `pass=true`
- paid RadarSimPy production gate stays `ready`
- paid readiness checkpoint stays `ready`
- PO-SBR parity stays `pass=true`
- frontend Playwright/operator evidence remains current

Treat this snapshot as not release-ready when any of the above flips red or stale.

## Remaining Release-Freeze Tasks

1. decide whether `HF-1` is default-required for the next cut
2. avoid adding more workflow micro-features unless they unblock validation
3. keep refreshing the same stable evidence set instead of creating parallel ad-hoc reports

## Recommended Handoff Rule

For handoff, send:

1. [Release Closure Handoff](294_release_closure_handoff_2026_03_08.md)
2. this snapshot doc
3. [Generated Reports Index](reports/README.md)
4. [canonical_release_candidate_subset_latest.json](reports/canonical_release_candidate_subset_latest.json)

That gives explanation, evidence routing, and one stable machine-readable status file.
