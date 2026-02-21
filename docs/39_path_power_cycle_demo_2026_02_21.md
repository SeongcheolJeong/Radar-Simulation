# Path Power Cycle Demo (2026-02-21)

## Objective

Verify executable cycle without external measured CSV:

1. ingest frames -> `path_list.json`
2. `path_list.json` -> `path_power_samples.csv`
3. `path_power_samples.csv` -> `path_power_fit_reflection.json`

## Output Root

- `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cycle_demo`

## Commands (executed)

1. Ingest:
   - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_hybrid_ingest_to_adc.py`
2. Sample CSV build:
   - `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_path_power_samples_from_path_list.py`
3. Fit:
   - `/Users/seongcheoljeong/Documents/Codex_test/scripts/fit_path_power_model_from_csv.py`

## Result Snapshot

- Sample rows: `8`
- Fit model: `reflection`
- Searched candidates: `6`
- Best params:
  - `range_power_exponent=2.5`
  - `gain_scale=9595214.603703225`
- Best metric:
  - `rmse_log=0.246728`

## Interpretation

This demo validates pipeline connectivity and artifacts, not final physics quality.
Final tuning quality must be assessed with real measured CSV collected from chamber/corridor scenarios.
