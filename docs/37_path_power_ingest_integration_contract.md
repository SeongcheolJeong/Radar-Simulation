# Path Power Ingest Integration Contract

## Goal

Apply fitted path-power model parameters during Hybrid frame ingest to reshape per-path amplitudes before FMCW synthesis.

## CLI Flags

`/Users/seongcheoljeong/Documents/Codex_test/scripts/run_hybrid_ingest_to_adc.py`

- `--path-power-fit-json /path/to/path_power_fit.json`
- `--path-power-apply-mode shape_only|replace`

## Fit JSON Requirement

The fit JSON must include:

- `fit.model` (`reflection` or `scattering`)
- `fit.best_params`

Model must match ingest `--mode`.

## Apply Modes

- `shape_only`:
  - keep original amplitude map scale
  - multiply by normalized fitted amplitude shape
- `replace`:
  - replace amplitude magnitude with fitted amplitude
  - preserve original sign

## Pipeline Surface

`run_hybrid_frames_pipeline` now exposes:

- `path_power_fit_json`
- `path_power_apply_mode`

Result metadata includes:

- `path_power_fit_enabled`
- `path_power_apply_mode`
- optional `path_power_fit_model`
- optional `path_power_fit_best_params`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_path_power_fit.py
```
