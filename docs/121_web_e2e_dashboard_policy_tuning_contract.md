# Web E2E Dashboard Policy Tuning Contract (M15.8)

## Goal

Allow radar developers to tune regression decision policy directly from dashboard and run compare/policy/session APIs with identical threshold intent.

Implementation:

- dashboard: `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`
- launcher: `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_dashboard_local.sh`

## UI Controls

- `regressionPolicyPresetSelect` (`default`, `strict`, `loose`)
- `requireParityPassCheck`
- `stopOnFirstFailCheck`
- `maxFailureCountInput`
- `rdShapeNmseMaxInput`
- `raShapeNmseMaxInput`

Preset changes update all control fields through `applyPolicyPresetToInputs`.

## API Wiring

- `POST /api/compare`
  - request includes tuned `thresholds`
- `POST /api/compare/policy`
  - request includes tuned `policy` and `thresholds`
- `POST /api/regression-sessions`
  - request includes tuned `policy`, `thresholds`, and `stop_on_first_fail`

## Query Params

- `policy_preset`
- `policy_require_parity`
- `policy_max_fail`
- `policy_rd_nmse`
- `policy_ra_nmse`
- `stop_on_first_fail`

## Validation

```bash
scripts/run_web_e2e_dashboard_local.sh 8095 8115
curl -s http://127.0.0.1:8115/health
curl -s "http://127.0.0.1:8095/frontend/avx_like_dashboard.html?summary=docs/reports/frontend_quickstart_v1.json"
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. dashboard HTML contains policy tuning controls
2. dashboard JS contains policy collector (`collectPolicyTuningConfig`) and preset applier
3. compare/policy/regression-session paths use the tuned payload fields
