# Web E2E Regression Gate Overview Contract (M15.7)

## Goal

Provide a compact gate-health summary in dashboard so radar developers can immediately see adopt/hold signal without opening each session/export JSON.

Implementation:

- dashboard: `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`

## Data Sources

- `GET /api/regression-sessions`
- `GET /api/regression-exports`

## Overview Outputs

- `regressionGateBadge`
  - `ADOPT` when latest session `all_pass=true` and `held_count=0`
  - `HOLD` when latest session has holds or is truncated
  - `REVIEW` when session exists but signal is mixed
  - `EMPTY` when latest session has no evaluated candidates
  - `NO DATA` when session history is empty
- KPI lines:
  - session/export counts
  - latest session id/time + adopted/held counts
  - linked export presence and row coverage
  - quick cue text for next action

## Update Triggers

- dashboard bootstrap
- `Refresh History`
- after `Run Regression Session`
- after `Export Session`

## Validation

```bash
scripts/run_web_e2e_dashboard_local.sh 8094 8114
curl -s http://127.0.0.1:8114/health
curl -s "http://127.0.0.1:8094/frontend/avx_like_dashboard.html?summary=docs/reports/frontend_quickstart_v1.json"
```

Pass criteria:

1. dashboard HTML contains gate overview elements (`regressionGateBadge`, `gateCueLine`)
2. dashboard JS contains gate evaluator (`updateRegressionGateOverview`)
3. history refresh path calls gate evaluator and updates badge/cue
