# Case-Partitioned Fit-Lock Search Contract

## Goal

Evaluate lock strategy in two stages:

1. global lock search across all cases
2. if global lock is not fit, fallback to family-partitioned lock search

This supports mixed strategy outputs (some families fit, others baseline).

## Core CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_case_partitioned_fit_lock_search.py \
  --case caseA=/path/to/source_pack_root::/path/to/baseline_replay_report.json \
  --case caseB=/path/to/source_pack_root::/path/to/baseline_replay_report.json \
  --case-family caseA=family_a \
  --case-family caseB=family_b \
  --fit-dir /path/to/fits \
  --fit-glob '*.json' \
  --objective-mode drift \
  --global-search-summary-json /path/to/existing_global_fit_lock_search_summary.json \
  --allow-unlocked \
  --output-root /path/to/case_partitioned_search_run \
  --output-summary-json /path/to/case_partitioned_search_summary.json
```

## Workflow

1. Resolve cases/family map and fit candidates.
2. Global stage:
   - reuse existing global summary if provided
   - otherwise run `run_measured_replay_fit_lock_search.py`.
3. If global selection is `fit`, finish with global strategy.
4. Else run family-level searches for each family subset.
5. Emit final strategy:
   - `global_fit_lock`
   - `family_partitioned_fit_lock`
   - `mixed_family_partitioned_lock`
   - `baseline_no_fit`

## Output

Summary JSON includes:

- `global_selection`
- per-family `selection_mode/recommendation/selected_fit_json`
- `final.strategy`
- `final.selected_fit_by_family`
- `reused_global_search_summary`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_case_partitioned_fit_lock_search.py
```

Validation checks:

- global baseline fallback path triggers family fallback runs
- final strategy is deterministic and JSON contract is stable
