# Radar Compensation Profile Lock Contract (M18.36)

## Goal

Tune `backend.radar_compensation` presets against measured/reference `radar_map.npz` artifacts and freeze profile-level defaults as lock JSON for reproducible golden-path/KPI matrix runs.

## Scope

- tuning core:
  - `src/avxsim/radar_compensation_tuning.py`
- tuning CLI:
  - `scripts/tune_radar_compensation_presets.py`
- lock-consumption path:
  - `scripts/run_scene_backend_golden_path.py` (`--radar-compensation-lock-json`)
  - `scripts/run_scene_backend_kpi_scenario_matrix.py` (pass-through)

## Tuning Inputs

1. `scene_json_template` with `backend.radar_compensation.enabled=true`
2. measured/reference `radar_map.npz`
3. candidate list JSON:
   - `candidates[*].name`
   - `candidates[*].patch` (deep-merged into base compensation config)

## Tuning Output

### 1) Tuning report JSON

- selected candidate name/score/metrics
- ranked candidate rows
- selected full compensation config

### 2) Profile lock JSON

- `profiles.<profile_id>.radar_compensation`
- `selected_candidate_name`
- `selected_score`

## Commands

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/tune_radar_compensation_presets.py \
  --profile-id single_target_ghost_comp_v1 \
  --scene-json-template /path/to/scene_template.json \
  --reference-radar-map-npz /path/to/measured_reference_radar_map.npz \
  --candidates-json /path/to/candidates.json \
  --output-root /path/to/tuning_outputs \
  --output-tuning-report-json /path/to/radar_comp_tuning_report.json \
  --output-lock-json /path/to/radar_comp_profile_lock.json
```

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_scene_backend_kpi_scenario_matrix.py \
  --strict-all-ready \
  --radar-compensation-lock-json /path/to/radar_comp_profile_lock.json \
  --output-root /path/to/scenario_matrix_outputs \
  --output-summary-json /path/to/scenario_matrix_summary.json
```
