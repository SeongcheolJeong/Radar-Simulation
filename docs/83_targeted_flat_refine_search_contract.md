# Targeted Flat-Refine Search Contract

## Goal

Run a low-degradation-focused constrained refit search by narrowing to flat-region presets and applying strict drift/non-degradation limits.

## Core CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_constrained_refit_drift_search.py \
  --baseline-mode provided \
  --case caseA=/path/to/source_pack_root::/path/to/baseline_replay_report.json \
  --csv-case familyA=/path/to/path_power_samples_a.csv \
  --csv-case familyB=/path/to/path_power_samples_b.csv \
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
  --output-root /path/to/targeted_flat_refine_run \
  --output-summary-json /path/to/targeted_flat_refine_summary.json
```

## Why This Variant

- avoids broad preset sweeps that repeatedly produce large degradation
- forces non-degrading eligibility at drift selector stage
- ensures all fit candidates are evaluated (no premature no-gain stop)

## Expected Outcome

- if at least one fit remains eligible under strict limits: `selection_mode=fit`
- otherwise deterministic fallback per preset: `selection_mode=baseline_no_fit`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_constrained_refit_drift_search.py
```

Validation checks:

- constrained run executes with drift/fit-proxy pass-through options
- row output contains valid per-preset artifacts and selection fields
