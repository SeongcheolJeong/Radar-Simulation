# Path Power Fit Selection Contract

## Goal

Select and lock model-wise fit JSONs from experiment summary output.

Typical use:

- multiple frame-count experiments were run
- need one stable fit JSON per model (`reflection`, `scattering`) for downstream tuned ingest

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/select_path_power_fit_from_experiment.py \
  --experiment-summary-json /path/to/xiangyu_label_fit_experiment_summary.json \
  --selection-strategy largest_frame_then_rmse \
  --output-dir /path/to/selected_fits \
  --output-summary-json /path/to/path_power_fit_selection_summary.json
```

## Selection Strategies

- `largest_frame_then_rmse` (default): choose best RMSE among runs at the largest frame-count
- `lowest_rmse`: choose best RMSE across all runs

## Outputs

- `<output-dir>/path_power_fit_reflection_selected.json`
- `<output-dir>/path_power_fit_scattering_selected.json`
- selection summary JSON

Each selected fit keeps original fit payload and appends `selection` metadata.

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_selection.py
```
