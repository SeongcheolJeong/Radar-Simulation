# EM Solver Packaging/License Boundary Contract (M18.38)

## Goal

Define a distributable-packaging boundary for optional EM solvers (`openEMS`, `gprMax`) used in AVx-lite antenna manifold generation.

This contract limits copyleft spillover risk by keeping EM solvers outside the core runtime path and shipping manifold assets as data artifacts.

## Scope

- policy artifact:
  - `docs/em_solver_packaging_policy.json`
- reference commit lock tracking:
  - `scripts/fetch_references.sh`
  - `external/reference-locks.md`
- deterministic validator:
  - `scripts/validate_em_solver_packaging_policy.py`
  - `scripts/validate_run_po_sbr_operator_handoff_closure_report.py`
- readiness checkpoint enforcement:
  - `scripts/run_po_sbr_myproject_readiness_checkpoint.sh`
  - `scripts/verify_po_sbr_operator_handoff_closure.sh`
  - `scripts/validate_po_sbr_operator_handoff_closure_report.py`
  - `scripts/run_po_sbr_readiness_checkpoint.sh`
- pre-push enforcement:
  - `.githooks/pre-push`
  - `scripts/validate_po_sbr_pre_push_hook_local_artifacts.py`
- post-change runtime-affecting classification:
  - `scripts/run_po_sbr_post_change_gate.py`

## Policy Requirements

1. Core runtime must stay solver-optional.
2. Product/distributable package must not bundle EM solver binaries by default.
3. Preferred mode is:
   - offline manifold precompute
   - ship only generated manifold assets (`.npz`/`.h5`)
4. Solver commits and licenses must be tracked in references/policy artifacts.
5. Legal review is required before distributable packaging that changes solver boundary assumptions.

## Machine-Readable Policy

`docs/em_solver_packaging_policy.json` is the authoritative policy snapshot and includes:

- `distribution_policy` gates
- `compliance_controls`
- `risk_classification`
- source repository/license inventory for `openEMS`, `CSXCAD`, `gprMax`

## Validation

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_em_solver_packaging_policy.py
```

Acceptance criteria:

- policy JSON schema/content passes validator
- `external/reference-locks.md` contains 40-hex commit locks for:
  - `openEMS`
  - `CSXCAD`
  - `gprMax`
- myproject readiness checkpoint emits EM policy validation provenance fields:
  - `em_solver_policy_json`
  - `em_solver_reference_locks_md`
  - `em_policy_validator_status`
  - `closure_report_validator_status`
  - `checkpoint_checks.closure_report_validator_ok`
- operator handoff closure emits EM policy validation provenance fields:
  - `em_solver_packaging_policy.policy_json`
  - `em_solver_packaging_policy.reference_locks_md`
  - `em_solver_packaging_policy.validator_status`
- main readiness checkpoint can run deterministic closure-report validator:
  - `scripts/validate_run_po_sbr_operator_handoff_closure_report.py`
- pre-push local-artifact deterministic validation must emit closure-report skip-only evidence markers:
  - `hook_skip_mode_matrix_verified: true`
  - `hook_closure_report_skip_only_verified: true`
  - `tracked_report_changes: 0`
- post-change gate treats EM policy + lock references as runtime-affecting inputs:
  - `docs/em_solver_packaging_policy.json`
  - `external/reference-locks.md`
