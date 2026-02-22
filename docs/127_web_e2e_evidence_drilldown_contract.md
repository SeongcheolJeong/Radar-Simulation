# Web E2E Regression Evidence Drill-Down Contract (M15.13)

## Goal

Provide a reviewer-oriented drill-down panel that pivots from regression session rows to policy-eval failure details without leaving dashboard.

Implementation:

- dashboard: `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`

## UI Controls

- panel title: `Evidence Drill-Down`
- badge/status:
  - `evidenceDrillBadge`
  - `evidenceDrillStatus`
- selectors:
  - `evidenceCandidateSelect`
  - `evidenceRuleSelect`
- quick actions:
  - `evidencePivotCompareBtn` (`Use Candidate`)
  - `evidenceOpenPolicyEvalBtn` (`Open Policy Eval`)
- details:
  - `evidenceSessionLine`
  - `evidenceCandidateLine`
  - `evidencePolicyEvalLine`
  - `evidenceDetailBox`

## Data Join Rules

1. choose focused session from `regressionSessionSelect` or `regressionSessionIdInput` (fallback latest)
2. filter rows where `gate_failed == true`
3. join row by `policy_eval_id` with `state.policyEvals`
4. rank rows by:
   - score: max(`value - limit`) across gate failures when numeric
   - fallback: `gate_failure_count`
5. populate candidate selector with ranked failed rows
6. populate rule selector from selected row gate failures

## Reviewer Loop Actions

- `Use Candidate`
  - set `compareCandRunInput` to selected evidence candidate run id
- `Open Policy Eval`
  - load cached policy-eval payload or fetch `GET /api/policy-evals/{policy_eval_id}`
  - render policy detail in existing compare result box
  - keep evidence panel synchronized

## Integration Points

- invoked after:
  - history refresh (`refreshRegressionHistoryViaApi`)
  - session load (`loadSelectedRegressionSessionViaApi`)
  - bootstrap initialization
- existing decision report evidence extraction now reuses focused-session failure collection path

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
scripts/run_web_e2e_dashboard_local.sh 8103 8123
curl -s "http://127.0.0.1:8103/frontend/avx_like_dashboard.html?summary=/docs/reports/frontend_quickstart_v1.json" | \
  rg -n "Evidence Drill-Down|evidenceCandidateSelect|evidenceRuleSelect|evidencePivotCompareBtn|evidenceOpenPolicyEvalBtn|updateEvidenceDrillDown"
```

Pass criteria:

1. dashboard HTML contains evidence drill-down controls and detail box
2. dashboard JS contains join/render/action handlers (`collectFocusedSessionFailureRows`, `updateEvidenceDrillDown`, `pivotCompareCandidateFromDrill`, `openEvidencePolicyEvalFromDrill`)
3. history/session refresh path updates evidence panel together with gate/audit updates
