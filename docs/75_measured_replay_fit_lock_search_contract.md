# Measured Replay Fit-Lock Search Contract

## Goal

Search fit-lock candidates efficiently under rerun-baseline policy, with early short-circuit when improvement is impossible.

## Core CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_measured_replay_fit_lock_search.py \
  --baseline-mode rerun \
  --case caseA=/path/to/source_pack_root \
  --case caseB=/path/to/source_pack_root \
  --fit-dir /path/to/selected_fits \
  --fit-dir /path/to/selected_fits_cross_family \
  --fit-dir /path/to/selected_fits_mixed \
  --min-improved-cases 1 \
  --require-full-case-coverage \
  --allow-unlocked \
  --output-root /path/to/fit_lock_search_run \
  --output-summary-json /path/to/fit_lock_search_summary.json
```

## Workflow

1. Build/resolve baseline replay per case (`rerun` or `provided` mode)
2. Compute improvement headroom count (`fail_count > 0` or `pass_rate < 1`)
3. Short-circuit condition:
   - if `min_improved_cases > headroom_count`, skip fit-aware batch execution
   - emit deterministic fallback selection (`baseline_no_fit`)
4. If not short-circuited:
   - run fit-aware batch
   - run policy gate
   - run fit-lock selector

## Output

Summary JSON includes:

- `cases_with_improvement_headroom`
- `short_circuit` and reason
- baseline case summaries
- selection (`fit` or `baseline_no_fit`)
- optional downstream artifact paths (`batch_summary_json`, `policy_gate_json`)

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_measured_replay_fit_lock_search.py
```

Validation checks:

- zero-headroom baseline triggers short-circuit
- selection is `baseline_no_fit` with fallback recommendation
