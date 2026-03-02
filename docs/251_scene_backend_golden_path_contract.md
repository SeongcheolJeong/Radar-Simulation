# Scene Backend Golden-Path Contract (M14.7)

## Goal

Provide one local command that reports execution progress for core scene backends used by radar developers:

1. `analytic_targets`
2. `sionna_rt`
3. `po_sbr_rt`

This command must run on this PC without macOS-to-Linux remote orchestration and emit a strict JSON report with backend status:

- `executed`
- `blocked`
- `failed`

## Scope

- runner: `scripts/run_scene_backend_golden_path.py`
- report validator: `scripts/validate_scene_backend_golden_path_report.py`
- runner self-validation: `scripts/validate_run_scene_backend_golden_path.py`

## Runner Contract

### Command

```bash
PYTHONPATH=src python3 scripts/run_scene_backend_golden_path.py \
  --radar-compensation-lock-json /path/to/radar_comp_profile_lock.json \
  --output-root data/runtime_golden_path/default \
  --output-summary-json docs/reports/scene_backend_golden_path_default.json
```

### Required output keys

- top-level:
  - `version`
  - `generated_at_utc`
  - `workspace_root`
  - `scene_equivalence_profile`
  - `equivalence_inputs`
  - `requested_backends`
  - `results`
  - `summary`
- per-backend (`results.<backend>`):
  - `status`
  - `blockers`
  - `diagnostics`
  - `scene_json`
  - `output_dir`
  - `path_list_json`
  - `adc_cube_npz`
  - `radar_map_npz`
  - `frame_count`
  - `path_count`
  - `runtime_resolution`
  - `error`

### Status semantics

1. `executed`
   - scene execution completed
   - output artifact paths exist
   - `frame_count > 0`, `path_count > 0`
2. `blocked`
   - prerequisites not met
   - `blockers` contains explicit reasons
3. `failed`
   - execution attempted but raised runtime error
   - `error` contains exception summary

### Progress summary semantics

- `summary.progress_ratio = executed_count / requested_count`
- `summary.po_sbr_migration_status`:
  - `closed_local_runtime` when `po_sbr_rt=executed`
  - `blocked` when `po_sbr_rt=blocked`
  - `failed` when `po_sbr_rt=failed`
  - `not_requested` when PO-SBR backend was not selected

### Default Scene Equivalence Profile

- `scene_equivalence_profile = single_target_range25_v1`
- policy:
  - align all backends to one-way `25m` target range and `+x` look direction
  - `sionna_rt`: sphere center offset by radius so front surface aligns at `25m`
  - `po_sbr_rt`: `phi/theta` aligned from target az/el, `min_range_m>=target_range`, amplitude floor + amplitude target enabled for parity-safe non-degenerate map generation

Supported profile ids:

1. `single_target_range25_v1`
2. `single_target_az20_range25_v1`
3. `single_target_vel3_range25_v1`
4. `dual_target_split_range25_v1` (multi-target realism informational profile)
5. `single_target_material_loss_range25_v1` (material-loss realism informational profile)
6. `mesh_dihedral_range25_v1` (dihedral mesh realism informational profile)
7. `mesh_trihedral_range25_v1` (trihedral mesh realism informational profile)
8. `single_target_ghost_comp_v1` (multipath/ghost-focused informational profile)
9. `single_target_clutter_comp_v1` (diffuse/clutter-focused informational profile)

Optional compensation lock override:

- `--radar-compensation-lock-json`:
  - when provided, profile-level compensation settings are overridden from lock payload for matching profile ids
  - report captures source in `equivalence_inputs.radar_compensation_source` and lock path in `equivalence_inputs.radar_compensation_lock_json`

## Validation

### 1) Contract validator

```bash
PYTHONPATH=src python3 scripts/validate_scene_backend_golden_path_report.py \
  --summary-json docs/reports/scene_backend_golden_path_default.json
```

### 2) Deterministic runner self-validation

```bash
PYTHONPATH=src python3 scripts/validate_run_scene_backend_golden_path.py
```

## Acceptance

M14.7 is accepted only if:

1. one command emits backend migration progress report for `analytic_targets`, `sionna_rt`, `po_sbr_rt`
2. report validator enforces schema and summary consistency
3. runner self-validation passes in deterministic fixture mode
4. report supports local triage of PO-SBR migration state (`closed_local_runtime|blocked|failed`)
