# Path Power Fit Selection (Cross-Family Ranking) Contract

## Goal

Lock model-wise fit JSONs from cross-family ranking summaries.

Input source is ranking output from:

- `rank_path_power_fits_by_cross_family.py`

Selection rule:

- choose `best` row per model from ranking summary (`cross_family_ranking_best_score`)

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/select_path_power_fit_from_cross_family_ranking.py \
  --ranking-summary reflection=/path/to/path_power_fit_cross_family_ranking_reflection.json \
  --ranking-summary scattering=/path/to/path_power_fit_cross_family_ranking_scattering.json \
  --output-dir /path/to/selected_fits_cross_family \
  --output-summary-json /path/to/path_power_fit_selection_cross_family_summary.json
```

## Outputs

- `<output-dir>/path_power_fit_reflection_selected.json`
- `<output-dir>/path_power_fit_scattering_selected.json`
- summary JSON

Each selected fit appends `selection` metadata:

- source ranking JSON
- selected strategy
- best-row score/pass/RA/RD deltas

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_selection_cross_family.py
```
