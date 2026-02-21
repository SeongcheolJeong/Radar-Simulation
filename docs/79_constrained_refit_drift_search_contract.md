# Constrained Refit Drift Search Contract

## Goal

Run bounded refit loops (preset parameter grids) and evaluate each preset with measured replay fit-lock search in drift objective mode.

## Core CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_constrained_refit_drift_search.py \
  --baseline-mode provided \
  --case caseA=/path/to/source_pack_root::/path/to/baseline_replay_report.json \
  --csv-case caseA=/path/to/path_power_samples.csv \
  --preset flat_fine_a \
  --preset flat_fine_b \
  --preset flat_fine_c \
  --max-no-gain-attempts 8 \
  --require-full-case-coverage \
  --drift-max-pass-rate-drop 0.0 \
  --drift-max-pass-count-drop-ratio 0.0 \
  --drift-max-fail-count-increase-ratio 0.0 \
  --drift-max-metric-drift 0.1 \
  --fit-proxy-max-range-exp 1.25 \
  --fit-proxy-max-azimuth-power 1.5 \
  --fit-proxy-min-weight 0.9 \
  --fit-proxy-max-weight 1.1 \
  --allow-unlocked \
  --output-root /path/to/constrained_refit_drift_search_run \
  --output-summary-json /path/to/constrained_refit_drift_search_summary.json
```

## Workflow

For each preset:

1. Run `run_path_power_fit_batch.py` with preset grid values
2. Collect generated `fit_json` artifacts
3. Run `run_measured_replay_fit_lock_search.py` with:
   - `--objective-mode drift`
   - provided case and fit candidates
   - fit-proxy and drift-limit constraints (optional)
4. Prevent premature candidate truncation by setting `--max-no-gain-attempts` high enough to cover candidate count
5. Store per-preset row with selection recommendation and score

After all presets:

- rank rows by recommendation priority and aggregate score
- emit `best` preset row

## Recommendation Rank

- `adopt_selected_fit_by_drift_objective` (best)
- `exploratory_fit_candidate_selected_by_drift`
- `fallback_to_baseline_no_fit`
- error/unknown

## Output

Summary JSON includes:

- `rows[]`: per-preset run results
- `best`: top-ranked preset row
- `preset_count`, `case_count`, `csv_case_count`
- per-row artifact pointers:
  - `fit_batch_summary_json`
  - `search_summary_json`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_constrained_refit_drift_search.py
```

Validation checks:

- synthetic pack + provided baseline pipeline runs end-to-end
- single-preset row is emitted with drift objective selection metadata
- `best` preset row is present and artifact paths are valid
