# Path Power Tuning Contract

## Goal

Tune reflection/scattering path-power parameters from measured amplitude samples.

## Input CSV Schema

Required columns:

- `range_m`
- `observed_amp`

Optional columns:

- `az_rad` (default `0.0`)
- `el_rad` (default `0.0`)
- `scenario_id`

`observed_amp` must be positive linear amplitude.

## Fit CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/fit_path_power_model_from_csv.py \
  --input-csv /path/to/path_power_samples.csv \
  --model scattering \
  --output-json /path/to/path_power_fit.json
```

## Main Parameters

- model: `reflection` or `scattering`
- shared:
  - `range_power_exponent`
  - `gain_scale` (fitted in log-domain)
- scattering-only:
  - `elevation_power`
  - `azimuth_mix`
  - `azimuth_power`

## Output JSON

- `fit.best_params`
- `fit.best_metrics`
- `fit.top_candidates`
- fit context (`fc_hz`, `pixel_width`, `pixel_height`, `searched_candidates`)

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_tuning.py
```
