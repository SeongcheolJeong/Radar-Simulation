# Measured Replay Fit-Lock Policy Selection Contract

## Goal

From rerun-baseline fit-aware batch results, choose an adoptable fit lock candidate or fallback to baseline no-fit when all candidates violate policy.

## Core CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/select_measured_replay_fit_lock_by_policy.py \
  --batch-summary-json /path/to/fit_aware_measured_replay_batch_summary.json \
  --output-json /path/to/measured_replay_fit_lock_selection.json \
  --max-pass-rate-drop 0.0 \
  --max-pass-count-drop 0 \
  --max-fail-count-increase 0 \
  --min-improved-cases 1 \
  --require-full-case-coverage
```

## Selection Rule

Per fit candidate:

- aggregate per-case policy checks:
  - no degradation (`pass_rate/pass_count/fail_count` deltas within limits)
  - improved case count
  - full coverage if required
- candidate is eligible only when all requirements pass

If one or more eligible candidates exist:

- select best by `(improved_case_count, total_pass_count_delta, total_pass_rate_delta)`

If none are eligible:

- fallback selection mode: `baseline_no_fit`

## Output

Summary JSON includes:

- `selection.selection_mode` (`fit` or `baseline_no_fit`)
- `selection.recommendation`
- `selection.selected_fit_json` (nullable)
- full per-fit rejection reasons and per-case deltas

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_select_measured_replay_fit_lock_by_policy.py
```

Validation checks:

- eligible fit is selected in positive synthetic batch
- fallback mode is selected when no fit satisfies minimum-improvement policy
