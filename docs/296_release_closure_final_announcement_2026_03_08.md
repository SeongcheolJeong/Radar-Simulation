# Release Closure Final Announcement

- Date: March 8, 2026
- Audience: internal release stakeholders, validators, operator handoff recipients
- Snapshot: [Release-Candidate Snapshot](291_release_candidate_snapshot_2026_03_08.md)
- One-page handoff: [Release Closure Handoff](294_release_closure_handoff_2026_03_08.md)
- Freeze rule: [Release Closure Freeze Note](298_release_closure_freeze_note_2026_03_08.md)

## Final Message

```text
[Release Closure] Default Release-Candidate Cut Is Green (2026-03-08)

The current default release-candidate cut is green and ready for handoff.

Default required checks:
1) FE-1 Graph Lab browser/operator flow
2) FE-2 frontend runtime payload -> provider info contract
3) RS-1 trial RadarSimPy layered parity
4) HF-2 PO-SBR parity/readiness path
5) RS-2 paid RadarSimPy production closure

Current status:
- canonical subset: pass=true
- PO-SBR parity: pass=true
- paid production gate: ready
- paid readiness checkpoint: ready
- Graph Lab Playwright/operator flow: current

HF-1 rule:
- HF-1 remains optional by default
- add it only when Sionna-style RT is part of the promised release story

Handoff bundle:
1) docs/294_release_closure_handoff_2026_03_08.md
2) docs/291_release_candidate_snapshot_2026_03_08.md
3) docs/reports/README.md
4) docs/reports/canonical_release_candidate_subset_latest.json
```

## Linked Evidence

- [canonical_release_candidate_subset_latest.json](reports/canonical_release_candidate_subset_latest.json)
- [graph_lab_playwright_e2e_latest.json](reports/graph_lab_playwright_e2e_latest.json)
- [scene_backend_parity_po_sbr_rt_latest.json](reports/scene_backend_parity_po_sbr_rt_latest.json)
- [radarsimpy_production_release_gate_paid_6m.json](reports/radarsimpy_production_release_gate_paid_6m.json)
- [radarsimpy_readiness_checkpoint_paid_6m.json](reports/radarsimpy_readiness_checkpoint_paid_6m.json)

## When Not To Send This As-Is

Do not send this unchanged if:

- canonical subset is no longer `pass=true`
- paid production gate or readiness checkpoint is not `ready`
- PO-SBR parity is not `pass=true`
- the release story has changed to require `HF-1`
