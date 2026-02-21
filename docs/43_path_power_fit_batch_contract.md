# Path Power Fit Batch Contract

## Goal

Run measured/path-list sample CSV fitting experiments in batch across:

- multiple scenario CSVs
- multiple models (`reflection`, `scattering`)

and emit:

- per-case fit JSON files
- aggregated batch summary for model comparison

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_path_power_fit_batch.py \
  --csv-case caseA=/path/to/case_a_path_power_samples.csv \
  --csv-case caseB=/path/to/case_b_path_power_samples.csv \
  --model reflection \
  --model scattering \
  --batch-id my_batch \
  --output-root /path/to/fit_batch_out \
  --output-summary-json /path/to/path_power_fit_batch_summary.json
```

## Outputs

- `<output-root>/fits/<case_label>_<model>.json`
- summary JSON (`path_power_fit_batch_summary.json`)
  - `runs[]`: one row per `(case, model)`
  - `by_model[model]`
    - `ranked_by_rmse_log`
    - `best_case`
    - `param_stats`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_batch.py
```
