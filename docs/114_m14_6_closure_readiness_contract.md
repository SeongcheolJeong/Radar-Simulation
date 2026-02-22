# M14.6 Closure Readiness Contract

## Goal

Provide a deterministic closure gate that tells whether M14.6 can be marked complete.

## Scope

Readiness checker:

1. verifies required M14.6 code/doc files exist
2. checks Linux strict pilot summary report existence
3. validates Linux summary with executed-report validator
4. emits machine-readable readiness JSON (`ready`, `missing_items`)

## Code Paths

- checker:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_m14_6_closure_readiness.py`
- validation:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_m14_6_closure_readiness.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_m14_6_closure_readiness.py
```

## Acceptance

Readiness contract is accepted only if:

1. checker emits deterministic schema and `missing_items` list
2. missing Linux report is surfaced as `linux_executed_report_missing`
3. once Linux executed report exists and validates, checker flips to `ready=true`
