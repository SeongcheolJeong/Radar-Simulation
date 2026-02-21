# Path Power Fit Cross-Family Ranking Contract

## Goal

Rank path-power fit candidates by cross-family comparator outcome, not only intra-case fit RMSE.

The ranking objective uses `run_hybrid_cross_family_fit_comparison.py` per candidate and scores:

- tuned pass/fail penalty
- RA mean delta (`tuned - baseline`)
- RD mean delta (`tuned - baseline`)

Lower score is better.

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/rank_path_power_fits_by_cross_family.py \
  --experiment-summary-json /path/to/xiangyu_label_fit_experiment_summary.json \
  --model reflection \
  --case-a-id case_a \
  --case-a-frames-root /path/to/case_a/frames \
  --case-a-radar-json /path/to/case_a/radar_parameters_hybrid.json \
  --case-b-id case_b \
  --case-b-frames-root /path/to/case_b/frames \
  --case-b-radar-json /path/to/case_b/radar_parameters_hybrid.json \
  --path-power-apply-mode shape_only \
  --frame-start 1 \
  --frame-end 64 \
  --camera-fov-deg 90 \
  --file-ext .npy \
  --output-root /path/to/ranking_run \
  --output-summary-json /path/to/path_power_fit_cross_family_ranking_summary.json
```

Optional dataset override inputs:

- `--amplitude-prefix`
- `--distance-prefix`
- `--distance-scale`

These are used when frame naming/semantics differ from mode defaults.

## Output

Summary JSON includes:

- `candidate_count`, `ok_count`
- `ranked[]` rows with candidate fit path and comparator metrics
- `best` row (top-ranked valid candidate)
- `all_rows[]` (including error rows)

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_cross_family_ranking.py
```
