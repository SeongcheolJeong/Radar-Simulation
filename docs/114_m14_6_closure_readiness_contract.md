# M14.6 Closure Readiness Contract

## Goal

Provide a deterministic closure gate that tells whether M14.6 can be marked complete.

## Scope

Readiness checker:

1. verifies required M14.6 code/doc files exist
2. checks Linux strict pilot summary report existence
3. validates Linux summary with executed-report validator
4. emits machine-readable readiness JSON (`ready`, `missing_items`)

Finalize helper:

1. runs readiness checker + executed-report validator
2. returns non-zero on not-ready state
3. optionally updates M14.6 markdown checklists/log sections when `--apply` is used

## Code Paths

- checker:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_m14_6_closure_readiness.py`
- finalize helper:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/finalize_m14_6_from_linux_report.py`
- validation:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_m14_6_closure_readiness.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_finalize_m14_6_from_linux_report.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_m14_6_closure_readiness.py
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_finalize_m14_6_from_linux_report.py
```

## Acceptance

Readiness contract is accepted only if:

1. checker emits deterministic schema and `missing_items` list
2. missing Linux report is surfaced as `linux_executed_report_missing`
3. once Linux executed report exists and validates, checker flips to `ready=true`
