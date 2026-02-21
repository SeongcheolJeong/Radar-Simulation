# Fit-Aware Replay Policy Gate Contract

## Goal

Decide whether current fit lock can be adopted for measured replay using rerun-baseline comparison and explicit non-degradation constraints.

## Core CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/evaluate_fit_aware_replay_policy_gate.py \
  --batch-summary-json /path/to/fit_aware_measured_replay_batch_summary.json \
  --output-json /path/to/fit_aware_replay_policy_gate_summary.json \
  --require-non-degradation-all-cases \
  --max-pass-rate-drop 0.0 \
  --max-pass-count-drop 0 \
  --max-fail-count-increase 0 \
  --min-improved-cases 1
```

## Policy Logic

Per attempt, non-degradation is satisfied only if all hold:

- `pass_rate_delta >= -max_pass_rate_drop`
- `pass_count_delta >= -max_pass_count_drop`
- `fail_count_delta <= max_fail_count_increase`

Per case:

- choose best eligible attempt by `(pass_count_delta, pass_rate_delta)`
- classify case as:
  - `improved_within_policy`
  - `non_degrading_no_gain`
  - `degrade_only`

Global gate:

- if `--require-non-degradation-all-cases` and any `degrade_only` exists -> fail
- if improved case count `< min_improved_cases` -> fail

Recommendation:

- `reject_fit_lock_due_to_degradation`
- `hold_fit_lock_no_material_gain`
- `accept_fit_lock`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_fit_aware_replay_policy_gate.py
```

Validation checks:

- non-degrading + improved synthetic batch -> `accept_fit_lock`
- degradation-only synthetic batch -> `reject_fit_lock_due_to_degradation`
