# Release Closure Handoff

- Date: March 8, 2026
- Status: current default release-candidate closure is green
- Scope: frontend/operator workflow, trial RadarSimPy parity, PO-SBR high-fidelity closure, paid RadarSimPy production closure
- Snapshot detail: [Release-Candidate Snapshot](291_release_candidate_snapshot_2026_03_08.md)
- HF-1 rule: [HF-1 Release Requirement Decision](293_hf1_release_requirement_decision_2026_03_08.md)

## Default Required Checks

Treat the current cut as release-ready only when all of these are green:

1. `FE-1` Graph Lab browser/operator flow
2. `FE-2` frontend runtime payload -> provider info contract
3. `RS-1` trial RadarSimPy layered parity
4. `HF-2` PO-SBR parity/readiness path
5. `RS-2` paid RadarSimPy production closure

## Optional Check For This Cut

- `HF-1` Sionna-style RT parity remains optional for the default cut.
- Promote it to required only when Sionna-style RT is part of the promised release story.

## Current Green Evidence

- [canonical_release_candidate_subset_latest.json](reports/canonical_release_candidate_subset_latest.json)
  - `pass=true`
- [graph_lab_playwright_e2e_latest.json](reports/graph_lab_playwright_e2e_latest.json)
  - browser/operator path current
- [scene_backend_parity_po_sbr_rt_latest.json](reports/scene_backend_parity_po_sbr_rt_latest.json)
  - `pass=true`
- [radarsimpy_production_release_gate_paid_6m.json](reports/radarsimpy_production_release_gate_paid_6m.json)
  - `production_gate_status=ready`
- [radarsimpy_readiness_checkpoint_paid_6m.json](reports/radarsimpy_readiness_checkpoint_paid_6m.json)
  - `overall_status=ready`

## Handoff Bundle

Send these together:

1. this one-page handoff doc
2. [Release-Candidate Snapshot](291_release_candidate_snapshot_2026_03_08.md)
3. [Generated Reports Index](reports/README.md)
4. [canonical_release_candidate_subset_latest.json](reports/canonical_release_candidate_subset_latest.json)

That bundle gives a short decision summary, detailed explanation, evidence routing, and one machine-readable status file.

## Refresh Command

Run this before handoff if you need to refresh the default closure evidence:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_canonical_release_candidate_subset.py \
  --output-json docs/reports/canonical_release_candidate_subset_latest.json
```

## Escalate Before Handoff If

- canonical subset is not `pass=true`
- paid RadarSimPy production gate or readiness checkpoint is not `ready`
- PO-SBR parity is not `pass=true`
- frontend Playwright/operator evidence is stale or failing
- the release story now includes Sionna-style RT, which would require re-evaluating `HF-1`
