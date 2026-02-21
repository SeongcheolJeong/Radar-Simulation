# Cross-Family Parity Shift Contract

## Goal

Compare cross-family parity gap change between baseline and tuned replay outputs.

Target question:

- Did tuned outputs reduce family-A vs family-B metric gap (especially RA metrics)?

## Input

Four replay reports:

- baseline family A
- baseline family B
- tuned family A
- tuned family B

Each report must follow measured replay format (`summary`, `cases[]`, `candidates[]`, `metrics`).

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/evaluate_cross_family_parity_shift.py \
  --baseline-a famA_base=/path/to/family_a_baseline_replay_report.json \
  --baseline-b famB_base=/path/to/family_b_baseline_replay_report.json \
  --tuned-a famA_tuned=/path/to/family_a_tuned_replay_report.json \
  --tuned-b famB_tuned=/path/to/family_b_tuned_replay_report.json \
  --metric ra_shape_nmse \
  --metric rd_shape_nmse \
  --quantiles 0.5,0.9,0.99 \
  --output-json /path/to/cross_family_parity_shift.json
```

## Output JSON

- `summaries.baseline.family_a|family_b`
- `summaries.tuned.family_a|family_b`
- `cross_family_gap.baseline[metric]`
  - `<qXX>_gap_abs`, `<qXX>_gap_signed`, `<qXX>_ratio_b_over_a`
- `cross_family_gap.tuned[metric]`
- `cross_family_gap.improvement[metric]`
  - `<qXX>_gap_reduction_abs`
  - `<qXX>_tuned_over_baseline_gap`
- `pass_rate_gap`
  - `baseline_abs`, `tuned_abs`, `reduction_abs`, `tuned_over_baseline`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_cross_family_parity_shift.py
```
