# Path Power Fit Lock A/B Comparison Contract

## Goal

Compare two locked fit assets under the same cross-family comparator setup:

- A: RMSE-only lock fit
- B: cross-family lock fit

The script runs comparator twice and emits a direct A/B delta report on tuned metrics.

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_path_power_fit_lock_ab_comparison.py \
  --case-a-id case_a \
  --case-a-frames-root /path/to/case_a/frames \
  --case-a-radar-json /path/to/case_a/radar_parameters_hybrid.json \
  --case-b-id case_b \
  --case-b-frames-root /path/to/case_b/frames \
  --case-b-radar-json /path/to/case_b/radar_parameters_hybrid.json \
  --mode reflection \
  --rmse-fit-json /path/to/path_power_fit_reflection_selected_rmse.json \
  --cross-family-fit-json /path/to/path_power_fit_reflection_selected_cross.json \
  --path-power-apply-mode shape_only \
  --frame-start 1 \
  --frame-end 64 \
  --camera-fov-deg 90 \
  --file-ext .npy \
  --output-root /path/to/ab_compare_run \
  --output-summary-json /path/to/path_power_fit_lock_ab_summary.json
```

Optional dataset override inputs:

- `--amplitude-prefix`
- `--distance-prefix`
- `--distance-scale`

## Output

Summary JSON contains:

- `runs.rmse_lock` and `runs.cross_family_lock`
  - tuned pass
  - tuned metrics
  - scalar score
- `ab_comparison.metric_delta_cross_minus_rmse`
- `ab_comparison.ra_summary`, `ab_comparison.rd_summary`
- `ab_comparison.winner_run_id`, `winner_reason`, `score_tie`

Lower score is better. On exact tie, current policy prefers `cross_family_lock`.

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_lock_ab_comparison.py
```
