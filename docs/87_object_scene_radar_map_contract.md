# Object Scene to Radar Map Contract

## Goal

Provide one entrypoint that turns object-scene input into:

1. propagation path list
2. raw ADC cube
3. radar map outputs (RD/RA)

Current backend scope:

- `hybrid_frames` (scene-level adapter over HybridDynamicRT frame outputs)
- `analytic_targets` (native non-frame backend stub for M11.2)
- `mesh_material_stub` (mesh/material-aware candidate backend for M12.0)
- `sionna_rt` (Sionna-exported path adapter backend for M13.1)

## Core Entry Points

- Module:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/scene_pipeline.py`
  - `run_object_scene_to_radar_map(...)`
  - `run_object_scene_to_radar_map_json(...)`
- CLI:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_object_scene_to_radar_map.py`

## Input JSON Schema (V0)

Required top-level keys:

- `backend`
- `radar`

`backend` required keys (`hybrid_frames`):

- `type`: one of `hybrid_frames`, `analytic_targets`, `mesh_material_stub`, `sionna_rt`
- `frames_root_dir`
- `radar_json_path`
- one of:
  - `frame_indices` (list of ints), or
  - `frame_start` + `frame_end`
- `camera_fov_deg`

`radar` required keys:

- `fc_hz`
- `slope_hz_per_s`
- `fs_hz`
- `samples_per_chirp`

Optional:

- `scene_id`
- `map_config` (`nfft_range`, `nfft_doppler`, `nfft_angle`, windows, `range_bin_limit`)
- pass-through ingest knobs (`mode`, `file_ext`, thresholds, `.ffd`, Jones, path-power fit)

## Outputs

Under `--output-dir`:

- `path_list.json`
- `adc_cube.npz`
- `radar_map.npz`
- `hybrid_estimation.npz` (optional, when `--run-hybrid-estimation`)

`radar_map.npz` contains:

- `fx_dop_win` (RD power map)
- `fx_ang` (RA power map)
- `metadata_json`

`path_list.json` path metadata (M11.3):

- `path_id`
- `material_tag`
- `reflection_order`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_to_radar_map.py
```

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_analytic_backend.py
```

## Known Limits (V0)

- `analytic_targets` backend is a deterministic stub (point-target kinematics), not mesh/material RT.
- `mesh_material_stub` uses simplified material weighting rules, not full geometric ray tracing.
- `sionna_rt` backend currently consumes exported Sionna-style paths JSON and does not embed Sionna runtime directly.
- Material-tagged propagation output columns are not finalized yet.
