# Hybrid Cross-Family Fit Comparison Contract

## Goal

Quantify whether selected path-power fit reduces cross-family drift in Hybrid ingest outputs.

Reference/candidate setup:

- reference: `case_a baseline`
- compare-1: `case_b baseline`
- compare-2: `case_b tuned` (with `--path-power-fit-json`)

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_hybrid_cross_family_fit_comparison.py \
  --case-a-id case_a \
  --case-a-frames-root /path/to/case_a/frames \
  --case-a-radar-json /path/to/case_a/radar_parameters_hybrid.json \
  --case-b-id case_b \
  --case-b-frames-root /path/to/case_b/frames \
  --case-b-radar-json /path/to/case_b/radar_parameters_hybrid.json \
  --path-power-fit-json /path/to/path_power_fit_reflection_selected.json \
  --path-power-apply-mode shape_only \
  --frame-start 1 \
  --frame-end 64 \
  --camera-fov-deg 90 \
  --mode reflection \
  --file-ext .npy \
  --output-root /path/to/hybrid_cross_family_run \
  --output-summary-json /path/to/hybrid_cross_family_fit_summary.json
```

## Output

Summary JSON contains:

- `comparisons.b_baseline_vs_a_baseline`
- `comparisons.b_tuned_vs_a_baseline`
- `cross_family_improvement.metric_delta`
  - `delta = tuned - baseline` (negative means improvement)
- `cross_family_improvement.ra_summary`
- `cross_family_improvement.rd_summary`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_cross_family_fit_comparison.py
```
