# Path Power Fit Selection (Mixed From A/B Reports) Contract

## Goal

Build final per-model locked fits by combining:

- RMSE-only locked fits
- cross-family locked fits
- A/B comparison reports (`rmse_lock` vs `cross_family_lock`)

Model selection rule:

- non-tie: use A/B winner
- tie: apply `--tie-policy`

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/select_path_power_fit_mixed_from_ab_reports.py \
  --ab-report reflection=/path/to/path_power_fit_lock_ab_comparison_reflection.json \
  --ab-report scattering=/path/to/path_power_fit_lock_ab_comparison_scattering.json \
  --rmse-selected-dir /path/to/selected_fits_rmse \
  --cross-selected-dir /path/to/selected_fits_cross_family \
  --tie-policy keep_rmse \
  --output-dir /path/to/selected_fits_mixed \
  --output-summary-json /path/to/path_power_fit_selection_mixed_summary.json
```

## Outputs

- `<output-dir>/path_power_fit_reflection_selected.json`
- `<output-dir>/path_power_fit_scattering_selected.json`
- mixed-selection summary JSON

Each output fit includes `selection` metadata (`source_type`, `source_fit_json`, `source_ab_report_json`).

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_selection_mixed_from_ab.py
```
