# Web E2E Dashboard Regression History Contract (M15.6)

## Goal

Expose regression-session/export history and artifact download actions directly in dashboard UI.

Implementation:

- dashboard: `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`
- launcher: `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_dashboard_local.sh`

## UI Controls

- `refreshRegressionHistoryBtn`
  - fetches `GET /api/regression-sessions` and `GET /api/regression-exports`
- `regressionSessionSelect`
  - loads selected session via `GET /api/regression-sessions/{session_id}`
- `exportRegressionBtn`
  - exports selected session via `POST /api/regression-exports`
- `regressionExportSelect`
  - loads selected export via `GET /api/regression-exports/{export_id}`
- `regressionDownloads`
  - renders links for:
    - `session_json`
    - `rows_csv`
    - `summary_index_json`
    - `package_json`

## Query Params

- `regression_session_id` (existing)
- `regression_export_id` (new)

On bootstrap, dashboard restores input values from query params and performs one history refresh.

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
scripts/run_web_e2e_dashboard_local.sh 8094 8114
curl -s http://127.0.0.1:8114/health
curl -s "http://127.0.0.1:8094/frontend/avx_like_dashboard.html?summary=docs/reports/frontend_quickstart_v1.json"
```

Pass criteria:

1. Health includes `regression_export_count`
2. Dashboard HTML contains history/export controls (`refreshRegressionHistoryBtn`, `exportRegressionBtn`)
3. Dashboard JS contains history/export handlers (`refreshRegressionHistoryViaApi`, `exportRegressionSessionViaApi`)
4. Existing run/compare/regression-session controls remain available
