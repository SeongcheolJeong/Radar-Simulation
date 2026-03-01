# Scene Backend KPI Scenario-Matrix Contract (M14.9/M14.10)

## Goal

Scale backend KPI/parity evidence from one equivalence scene to multiple profile families and track where high-fidelity backend behavior diverges from analytic equivalence expectations, while keeping strict release-gate profiles isolated from informational realism profiles.

## Scope

- matrix runner: `scripts/run_scene_backend_kpi_scenario_matrix.py`
- matrix validator: `scripts/validate_scene_backend_kpi_scenario_matrix_report.py`
- deterministic matrix validation: `scripts/validate_run_scene_backend_kpi_scenario_matrix.py`

## Profiles (default)

1. `single_target_range25_v1` (`equivalence_strict`, gate-required)
2. `single_target_az20_range25_v1` (`equivalence_strict`, gate-required)
3. `single_target_vel3_range25_v1` (`equivalence_strict`, gate-required)
4. `dual_target_split_range25_v1` (`realism_informational`)
5. `single_target_material_loss_range25_v1` (`realism_informational`)
6. `mesh_dihedral_range25_v1` (`realism_informational`)
7. `mesh_trihedral_range25_v1` (`realism_informational`)

## Runner Contract

### Command

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_scene_backend_kpi_scenario_matrix.py \
  --strict-all-ready \
  --output-root data/runtime_golden_path/scenario_matrix_local_2026_03_01_v4 \
  --output-summary-json docs/reports/scene_backend_kpi_scenario_matrix_local_2026_03_01_v4.json
```

### Required output keys

- top-level:
  - `version`
  - `python_bin`
  - `profiles`
  - `gate_profile_families`
  - `output_root`
  - `matrix_status` (`ready|blocked|failed`)
  - `summary`
  - `rows`
- per-row:
  - `profile`
  - `profile_family`
  - `gate_required`
  - `golden_summary_json`
  - `kpi_summary_json`
  - `run_steps`
  - `run_ok`
  - `campaign_status`
  - `blockers`
  - `parity_fail_count`
  - `divergence_pairs`

## Status semantics

- `ready`: no run failures and all `gate_required=true` profiles are `campaign_status=ready`
- `blocked`: no run failures, but at least one `gate_required=true` profile is not `ready`
- `failed`: at least one profile run/validation failed

## Validation

### 1) Report schema validator

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_scene_backend_kpi_scenario_matrix_report.py \
  --summary-json docs/reports/scene_backend_kpi_scenario_matrix_local_2026_03_01_v4.json
```

### 2) Deterministic runner validation

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_run_scene_backend_kpi_scenario_matrix.py
```

## Acceptance

M14.9/M14.10 is accepted only if:

1. scenario-matrix report is generated with default profile families (strict + informational)
2. each profile includes explicit family and gate-required flags
3. divergence pairs are captured when parity fails
4. matrix status is computed from gate-required profiles, with informational divergence still visible
5. matrix schema validation and deterministic matrix runner validation pass
