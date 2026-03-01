# PO-SBR Physical Full-Track Bundle Contract (M14.11)

## Goal

Emit one local readiness report for radar developers that proves this PC can execute strict-equivalence and realism mesh/material PO-SBR scenarios end-to-end without macOS<->Linux remote orchestration.

## Scope

- bundle runner: `scripts/run_po_sbr_physical_full_track_bundle.py`
- bundle validator: `scripts/validate_po_sbr_physical_full_track_bundle_report.py`
- deterministic runner validation: `scripts/validate_run_po_sbr_physical_full_track_bundle.py`

## Required profile set (default)

1. `single_target_range25_v1` (gate-required)
2. `single_target_az20_range25_v1` (gate-required)
3. `single_target_vel3_range25_v1` (gate-required)
4. `dual_target_split_range25_v1` (informational)
5. `single_target_material_loss_range25_v1` (informational)
6. `mesh_dihedral_range25_v1` (informational, PO-SBR `dihedral.obj`)
7. `mesh_trihedral_range25_v1` (informational, PO-SBR `trihedral.obj`)

Gate family default:

- `equivalence_strict`

## Runner Contract

### Command

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_po_sbr_physical_full_track_bundle.py \
  --strict-ready \
  --output-root data/runtime_golden_path/po_sbr_full_track_local_2026_03_01 \
  --matrix-summary-json docs/reports/scene_backend_kpi_scenario_matrix_local_2026_03_01_v4.json \
  --output-summary-json docs/reports/po_sbr_physical_full_track_bundle_local_2026_03_01.json
```

### Required output keys

- top-level:
  - `version`
  - `generated_at_utc`
  - `workspace_root`
  - `purpose`
  - `required_profiles`
  - `gate_profile_families`
  - `missing_required_profiles`
  - `full_track_status` (`ready|blocked`)
  - `blockers`
  - `source_matrix_summary_json`
  - `matrix_status`
  - `matrix_summary`
  - `matrix_run`
  - `rows`
  - `summary`
- per-row:
  - `profile`
  - `profile_family`
  - `gate_required`
  - `run_ok`
  - `campaign_status`
  - `parity_fail_count`
  - `golden_summary_json`
  - `kpi_summary_json`
  - `po_sbr_status`
  - `po_sbr_path_count`
  - `po_sbr_scene_json`
  - `po_sbr_geometry_path`

## Status semantics

- `full_track_status=ready`
  - matrix run completed
  - no required profile missing
  - matrix gate state ready (`gate_blocked_profile_count=0`)
  - no matrix profile failures
- `full_track_status=blocked`
  - any of the above is not satisfied

`--strict-ready` behavior:

- report is written first
- command exits non-zero when `full_track_status != ready`

## Validation

### 1) Bundle report validator

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_physical_full_track_bundle_report.py \
  --summary-json docs/reports/po_sbr_physical_full_track_bundle_local_2026_03_01.json \
  --require-ready
```

### 2) Deterministic runner validation

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_run_po_sbr_physical_full_track_bundle.py
```

## Acceptance

M14.11 is accepted only if:

1. bundle report is generated from local matrix run on this PC
2. required full-track profile set is present with no missing entries
3. strict gate profiles remain ready
4. realism mesh/material profiles are included and PO-SBR execution evidence is captured
5. bundle report validator and deterministic runner validation both pass
