# HF-1 Release Requirement Decision

- Date: March 8, 2026
- Scope: whether `HF-1` (`scene_backend_parity_sionna_rt_latest.json`) should move from optional to default-required in the release-candidate subset

## Decision

- `HF-1` remains optional for the default release-candidate subset.
- Promote `HF-1` to required only when the release story explicitly depends on the Sionna-style RT backend.

## Rationale

- the default closure path is already green with `FE-1`, `FE-2`, `RS-1`, `HF-2`, and `RS-2`
- `HF-2` is the higher-priority high-fidelity closure path for the current operator/runtime release story
- `HF-1` stable evidence is green, but it is not on the current primary release-critical runtime path
- keeping `HF-1` optional lowers closure cost while preserving an explicit promotion rule

## Current Evidence

- [scene_backend_parity_sionna_rt_latest.json](reports/scene_backend_parity_sionna_rt_latest.json)
  - `pass=true`
- [canonical_release_candidate_subset_latest.json](reports/canonical_release_candidate_subset_latest.json)
  - green with `with_sionna=false`

## Promote HF-1 To Required When

- release notes or operator docs expose Sionna-style RT as a primary supported path
- frontend or orchestration defaults select the Sionna-style RT path for user-facing workflows
- delivery acceptance depends on Sionna-style output, parity, or performance claims

## Keep HF-1 Optional When

- it remains an available but not default runtime/backend path
- PO-SBR remains the main high-fidelity closure path
- current release acceptance does not claim Sionna-style RT as mandatory

## Re-Evaluation Rule

Revisit this decision when backend defaults, runtime policy, or release scope changes.

## Recommended Operator Wording

Use this wording in snapshots or handoff notes:

> Default release closure requires `HF-2`; add `HF-1` when the Sionna-style RT path is part of the promised release story.
