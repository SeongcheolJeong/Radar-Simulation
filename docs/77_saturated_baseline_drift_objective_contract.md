# Saturated Baseline Drift Objective Contract

## Goal

When replay baseline is saturated (`pass_rate=1.0`) and improvement objective has no headroom, rank fit candidates by least distortion (drift objective) instead of improvement count.

## Core CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/select_measured_replay_fit_lock_by_drift_objective.py \
  --batch-summary-json /path/to/fit_aware_measured_replay_batch_summary.json \
  --output-json /path/to/measured_replay_fit_lock_drift_selection.json \
  --metric ra_shape_nmse \
  --metric rd_shape_nmse \
  --drift-quantile 0.9 \
  --require-full-case-coverage
```

## Objective

Per fit candidate, aggregate:

- pass-rate drop penalty
- pass-count drop ratio penalty
- fail-count increase ratio penalty
- parity metric drift penalty (`|ratio-1|` at selected quantile)

Total score:

- weighted sum of the penalties above
- lower score is better

## Recommendation Rule

- if selected fit has zero degradation terms:
  - `adopt_selected_fit_by_drift_objective`
- if selected fit still degrades pass/fail:
  - `exploratory_fit_candidate_selected_by_drift`
- if no eligible fit:
  - fallback `baseline_no_fit`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_select_measured_replay_fit_lock_by_drift_objective.py
```

Validation checks:

- lower-drift fit is selected in synthetic non-degrading case
- strict drift constraint triggers baseline fallback
