# RadarSimPy Periodic Parity Lock Contract (M13.3)

## Goal

Add periodic parity-lock automation that compares candidate ADC outputs against locked RadarSimPy-view references (`channel, pulse, sample`) and emits deterministic gate decisions.

## Scope

- periodic lock core:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/radarsimpy_periodic_lock.py`
- runner CLI:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_radarsimpy_periodic_parity_lock.py`

## Manifest Contract

Top-level:

- `cases`: non-empty list

Per-case required:

- `case_id` (optional, auto if missing)
- `candidate_adc_npz`
- `reference_view_npz`

Per-case optional:

- `candidate_adc_key` (default `adc`)
- `candidate_adc_order` (default `sctr`)
- `reference_view_key` (default `view`)

## Metrics and Gate

Computed metrics:

- `view_nmse`
- `power_nmse`
- `mean_abs_error`
- `max_abs_error`
- `complex_corr_abs`

Default thresholds:

- `view_nmse_max`
- `power_nmse_max`
- `mean_abs_error_max`
- `max_abs_error_max`
- `complex_corr_abs_min`

Gate passes only if all cases pass threshold checks.

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_radarsimpy_periodic_parity_lock.py
```

## Acceptance

M13.3 is accepted only if:

1. periodic lock runner produces pass/fail summary with deterministic thresholds
2. validation covers both pass-only and mixed(pass+fail) case manifests
