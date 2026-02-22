# Web E2E Decision Report Failure Evidence Contract (M15.12)

## Goal

Auto-include top gate-failure evidence lines in dashboard decision-report markdown export so reviewers can see concrete failure signals without opening raw policy payloads first.

Implementation:

- dashboard: `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`

## Scope

- extend `buildDecisionReportTemplateMarkdown()` output with evidence section
- evidence source is current focus regression session rows + joined `state.policyEvals`
- include deterministic fallback when no evidence exists

## Evidence Selection Rules

1. pick focused regression session (`regressionSessionSelect` or `regressionSessionIdInput`, fallback latest)
2. filter rows with `gate_failed == true`
3. join each row with `policy_eval_id` payload (`gate_failures[]`)
4. score/rank failures:
   - numeric score: `value - limit` when both numeric
   - fallback score: `gate_failure_count` or `1`
5. emit top-N (default 8) lines to markdown

## Added Functions

- `collectTopFailureEvidenceRows(maxItems)`
- `formatEvidenceValue(v)`

## Markdown Additions

- section: `## Top Failure Evidence (Auto-Extracted)`
- metadata lines:
  - `source_session`
  - `source_policy_eval_count`
- item line format:
  - `candidate=<id> | eval=<policy_eval_id> | rule=<rule>(<metric>) | value=<v> | limit=<v> | row_failures=<count>`
- fallback line:
  - `none (no gate-failure evidence found for current focus session)`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
rg -n "collectTopFailureEvidenceRows|formatEvidenceValue|Top Failure Evidence \\(Auto-Extracted\\)|no gate-failure evidence found" /Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html
```

Pass criteria:

1. dashboard JS contains evidence collector/formatter helpers
2. decision report markdown builder includes `Top Failure Evidence (Auto-Extracted)` section
3. no-evidence fallback and evidence item formatting are both present in template logic
