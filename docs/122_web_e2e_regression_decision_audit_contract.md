# Web E2E Regression Decision Audit Contract (M15.9)

## Goal

Provide an at-a-glance audit panel that explains why regression decisions are trending toward adopt/hold, including rule-level failure concentration.

Implementation:

- dashboard: `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`

## Data Inputs

- `GET /api/regression-sessions`
- `GET /api/regression-exports`
- `GET /api/policy-evals`

## Panel Elements

- `decisionAuditBadge`
  - `STABLE`, `RISK`, `REVIEW`, `EMPTY`, `NO DATA`
- `auditSummaryLine`
  - focus session id/time, evaluated/held counts, export linkage
- `auditTrendLine`
  - recent hold-rate trend (avg/newest/oldest)
- `auditRuleHistogram`
  - top failing rules aggregated from `policy_eval.gate_failures[].rule`
- `auditHotCandidateLine`
  - candidate row with max `gate_failure_count`

## Update Triggers

- bootstrap
- history refresh
- session selection change

## Validation

```bash
scripts/run_web_e2e_dashboard_local.sh 8097 8117
curl -s http://127.0.0.1:8117/health
curl -s "http://127.0.0.1:8097/frontend/avx_like_dashboard.html?summary=docs/reports/frontend_quickstart_v1.json"
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. dashboard HTML includes audit controls (`decisionAuditBadge`, `auditRuleHistogram`, `auditHotCandidateLine`)
2. dashboard JS includes audit evaluator (`updateRegressionDecisionAudit`)
3. history refresh loads `policy-evals` and updates audit panel from live API data
