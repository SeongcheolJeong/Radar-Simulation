# Constrained Refit Consistency Gate Contract

## Goal

Apply a deterministic multi-case accept/reject gate to constrained-refit preset results and decide:

- adopt best preset fit
- fallback to baseline (`baseline_no_fit`)

## Core CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/evaluate_constrained_refit_consistency_gate.py \
  --constrained-summary-json /path/to/constrained_refit_drift_search_summary.json \
  --output-json /path/to/constrained_refit_consistency_gate_summary.json \
  --max-total-pass-rate-drop 0.0 \
  --max-total-pass-count-drop-ratio 0.0 \
  --max-total-fail-count-increase-ratio 0.0 \
  --max-metric-drift-mean 0.1
```

## Eligibility Rule (per preset)

1. search row is valid (`search_ok=true`, `selection_mode=fit`)
2. recommendation allowed:
   - default: `adopt_selected_fit_by_drift_objective` only
   - optional exploratory allowance with `--allow-exploratory-recommendation`
3. full case coverage (`coverage_count == case_count`)
4. aggregate degradation/drift constraints:
   - `total_pass_rate_drop <= max_total_pass_rate_drop`
   - `total_pass_count_drop_ratio <= max_total_pass_count_drop_ratio`
   - `total_fail_count_increase_ratio <= max_total_fail_count_increase_ratio`
   - `metric_drift_mean <= max_metric_drift_mean`

Optional:

- enforce policy-gate pass with `--require-policy-gate-pass`

## Selection Rule

- eligible presets ranked by:
  1. recommendation priority
  2. aggregate score (lower is better)
  3. preset index (stable tie-break)
- if no eligible preset: fallback `baseline_no_fit`

## Output

Summary JSON includes:

- `gate_failed`, `recommendation`, `selection_mode`
- `selected_preset`, `selected_fit_json`
- `rows[]` with per-preset:
  - eligibility
  - rejection reasons
  - drop/drift diagnostics

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_evaluate_constrained_refit_consistency_gate.py
```

Validation checks:

- success case selects `flat` preset
- strict threshold case falls back to `baseline_no_fit`
