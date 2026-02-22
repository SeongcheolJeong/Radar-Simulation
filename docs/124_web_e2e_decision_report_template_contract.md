# Web E2E Decision Report Template Export Contract (M15.11)

## Goal

Generate a reusable markdown handoff skeleton from dashboard in one click, using current regression gate/audit state and artifact pointers.

Implementation:

- dashboard: `/Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`

## UI Controls

- `exportDecisionReportBtn`
- `decisionReportStatus`
- `decisionReportFileBox`

## Export Flow

1. collect current UI/state snapshot:
   - baseline/session/export ids
   - policy tuning values
   - gate overview lines
   - decision audit lines
   - review bundle/artifact pointers
2. build markdown via `buildDecisionReportTemplateMarkdown`
3. download `.md` using browser blob download
4. best-effort clipboard copy of markdown body
5. update status/file UI

## Markdown Sections

- metadata
- candidate context
- policy configuration
- gate overview snapshot
- decision audit snapshot
- artifact pointers
- reviewer checklist
- decision placeholders (`final_decision`, `owner`, `due_date`, `notes`)

## Validation

```bash
scripts/run_web_e2e_dashboard_local.sh 8099 8119
curl -s http://127.0.0.1:8119/health
curl -s "http://127.0.0.1:8099/frontend/avx_like_dashboard.html?summary=docs/reports/frontend_quickstart_v1.json"
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. dashboard HTML includes decision-report controls (`exportDecisionReportBtn`, `decisionReportFileBox`)
2. dashboard JS includes markdown exporter (`buildDecisionReportTemplateMarkdown`, `exportDecisionReportTemplate`)
3. export action produces downloadable markdown template and updates status UI
