# Radar Compensation Layer Contract (M18.34)

## Goal

Add an explicit radar-specific compensation boundary between `PathList` generation and ADC synthesis for AVx-lite realism controls.

Layer scope:

1. material/RCS scaling
2. wideband FMCW correction
3. manifold complex gain injection
4. diffuse path spawning
5. clutter path spawning

## Module

- implementation:
  - `src/avxsim/radar_compensation.py`
- scene-pipeline integration:
  - `src/avxsim/scene_pipeline.py`
  - applied before `synth_fmcw_tdm(...)` for:
    - `analytic_targets`
    - `mesh_material_stub`
    - `sionna_rt`
    - `po_sbr_rt`
    - `radarsimpy_rt`

## Backend Config Contract

`scene.json` backend optional object:

- `backend.radar_compensation`
  - `enabled: bool`
  - `random_seed: int | null`
  - `default_material_model`
  - `material_models` (by `material_tag`)
  - `wideband`
  - `manifold`
    - supports optional complex-manifold asset fields:
      - `asset_path` (`.npz` / `.h5` / `.hdf5`)
      - `asset_frequency_hz`
      - `asset_gain_scale`
      - `asset_tx_pol_weights`
      - `asset_rx_pol_weights`
  - `diffuse`
  - `clutter`

If omitted, compensation is bypassed and baseline behavior is unchanged.

## Metadata Contract

`radar_map.npz` `metadata_json` includes `compensation_summary`:

- `enabled`
- `input_path_count`
- `output_path_count`
- `added_diffuse_path_count`
- `added_clutter_path_count`
- `wideband_enabled`
- `manifold_enabled`
- `manifold_asset_enabled`
- `manifold_asset_path`
- `manifold_asset_frequency_hz`
- `manifold_asset_gain_scale`

## Validation

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_scene_radar_compensation_layer.py
```
