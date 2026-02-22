# Web E2E Graph Audit Drilldown + Import-History Persistence (M17.33)

## Goal

Make filter-import history practically reviewable and resumable across reloads.

1. drill down into per-audit-entry full detail (`selected/added/removed names`)
2. export and copy audit evidence for team handoff
3. persist undo/redo/audit stacks in bounded localStorage

Implementation:

- audit drilldown + history persistence:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- history persistence:
  - storage key: `graph_lab_contract_overlay_filter_import_history_v1`
  - restore/save helpers:
    - `loadFilterImportHistoryState`
    - `saveFilterImportHistoryState`
  - bounded state synced:
    - `filterImportUndoStack`
    - `filterImportRedoStack`
    - `filterImportAuditTrail`
- audit detail drilldown:
  - active row selector: `activeFilterImportAuditId`
  - detail formatter: `buildFilterImportAuditDetailText`
  - detail panel key: `co_filter_import_audit_detail`
  - row list container/key:
    - `co_filter_import_audit_rows`
    - `co_filter_import_audit_row_<idx>`
  - row summary includes compact selected-name preview (`names:...`)
- audit handoff actions:
  - `Copy Audit Detail` (`co_filter_import_audit_copy`)
  - `Export Audit JSON` (`co_filter_import_audit_export`)
  - export serializer:
    - `buildFilterImportAuditExportBundle`
    - `serializeFilterImportAuditExportBundle`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8164 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8144
curl -s "http://127.0.0.1:8144/frontend/graph_lab/panels.mjs" | rg -n "CONTRACT_OVERLAY_FILTER_IMPORT_HISTORY_KEY|loadFilterImportHistoryState|saveFilterImportHistoryState|buildFilterImportAuditDetailText|buildFilterImportAuditExportBundle|serializeFilterImportAuditExportBundle|activeFilterImportAuditId|co_filter_import_audit_controls|co_filter_import_audit_copy|co_filter_import_audit_export|co_filter_import_audit_rows|co_filter_import_audit_detail|co_filter_import_audit_row_|names:|Undo Import|Redo Import|undo/redo depth"
```

Pass criteria:

1. history persistence tokens are present
2. audit drilldown and handoff action tokens are present
3. backend regression remains pass
