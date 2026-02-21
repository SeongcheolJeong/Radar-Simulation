# Measured Replay Fit-Change Impact Contract

## Goal

Determine whether changing path-power fit lock assets can affect measured replay outputs for given measured replay plans.

This is a dependency-gate step to avoid meaningless replay re-runs.

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/analyze_measured_replay_fit_change_impact.py \
  --plan-json /path/to/measured_replay_plan_a.json \
  --plan-json /path/to/measured_replay_plan_b.json \
  --fit-dir /path/to/selected_fits \
  --fit-dir /path/to/selected_fits_cross_family \
  --fit-dir /path/to/selected_fits_mixed \
  --output-json /path/to/measured_replay_fit_change_impact.json
```

## Output

Summary JSON includes:

- `predicted_noop_all_plans`
- `recommendation`
- per plan/pack:
  - candidate count
  - fit dependency detected flag
  - evidence entries (if detected)

## Decision Rule

- If `predicted_noop_all_plans=true`, skip measured replay rerun for fit-lock changes.
- If any plan is impacted, rerun only impacted plans.

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_measured_replay_fit_change_impact.py
```
