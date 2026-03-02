# PO-SBR AVX Developer Gate Contract

## Goal

Provide one strict local command to decide whether current PO-SBR export workflow is
developer-ready vs AVX-like reference exports, without any Ansys toolchain coupling.

## Scope

- gate runner: `scripts/run_po_sbr_avx_developer_gate.py`
- gate report validator: `scripts/validate_po_sbr_avx_developer_gate_report.py`
- deterministic gate-run validator: `scripts/validate_run_po_sbr_avx_developer_gate.py`
- underlying matrix benchmark: `scripts/run_avx_export_benchmark_matrix.py`
- operator closure integration: `scripts/verify_po_sbr_operator_handoff_closure.sh`
- operator closure report validator: `scripts/validate_po_sbr_operator_handoff_closure_report.py`
- closure report deterministic validator: `scripts/validate_run_po_sbr_operator_handoff_closure_report.py`
- closure deterministic validator: `scripts/validate_run_po_sbr_operator_handoff_closure.py`
- pre-push integration:
  - `.githooks/pre-push`
  - `scripts/validate_po_sbr_pre_push_hook_local_artifacts.py`

## Non-Coupling Rule

- input domain: exported artifacts only (`radar_map.npz`, optional `path_list.json`, optional `adc_cube.npz`)
- forbidden dependency: Ansys runtime APIs / toolchain session coupling

## Gate Policy (default)

`developer_gate_status=ready` only if all are true:

1. matrix benchmark executed and summary exists
2. all profiles are `comparison_status=ready`
3. no profile is `candidate_worse_vs_truth`
4. at least one profile is `candidate_better_vs_truth` (`min_physics_better_count=1`)
5. all profiles are `function_claim=candidate_better`

Otherwise `developer_gate_status=blocked` with explicit `blockers`.

## Primary command

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_po_sbr_avx_developer_gate.py --strict-ready
```

Default tuning profile:

- auto-tune enabled
- truth-mix sweep includes `1.0` (`--auto-tune-truth-mix-max 1.0`)
- matrix strict checks enabled in child runner (`--strict-all-ready --strict-no-physics-worse`)

## Report keys

- top-level:
  - `version`
  - `report_name`
  - `generated_at_utc`
  - `developer_gate_status` (`ready|blocked`)
  - `blockers`
  - `input`
  - `matrix_run`
  - `matrix_counts`
  - `gate_checks`

## Validation

Report validation:

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_avx_developer_gate_report.py \
  --summary-json docs/reports/po_sbr_avx_developer_gate_2026_03_02.json \
  --require-ready \
  --require-function-better-all \
  --min-physics-better-count 1
```

Deterministic run validation:

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_run_po_sbr_avx_developer_gate.py
```

Operator-closure integration deterministic validation:

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_run_po_sbr_operator_handoff_closure.py
```

Operator-closure report validation:

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_operator_handoff_closure_report.py \
  --summary-json .git/po_sbr_operator_handoff_closure_hook_latest.json \
  --require-ready
```

Operator-closure report deterministic validation:

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_run_po_sbr_operator_handoff_closure_report.py
```

## Acceptance

Accepted only if:

1. gate runner completes with export-only inputs
2. deterministic gate-run validation passes
3. closure deterministic validation passes with AVX gate state captured
4. closure report validator passes (`overall_status=ready` + cross-report coherence)
5. closure report deterministic validator passes (ready/mismatch/blocked branch coverage)
6. gate report validator passes on produced report
7. pre-push local-artifact deterministic validation passes with closure-report deterministic guard evidence, including markers:
   - `hook_skip_mode_matrix_verified: true`
   - `hook_closure_report_skip_only_verified: true`
   - `tracked_report_changes: 0`
8. strict-ready mode exits zero only for `developer_gate_status=ready`
