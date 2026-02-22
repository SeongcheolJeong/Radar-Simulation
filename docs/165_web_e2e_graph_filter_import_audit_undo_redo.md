# Web E2E Graph Import Audit Trail + Multi-Level Undo/Redo (M17.32)

## Goal

Increase operator safety and traceability for filter preset transfer operations.

1. keep import operation audit summaries in overlay
2. support multi-level undo/redo for import-applied state changes
3. surface change counts (`+added/~changed/-removed`) on each import

Implementation:

- import history + audit wiring:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- snapshot/diff helpers:
  - `buildFilterPresetStateSnapshot`
  - `compactNameList`
- history state:
  - undo stack: `filterImportUndoStack`
  - redo stack: `filterImportRedoStack`
  - audit trail: `filterImportAuditTrail`
  - bounded depth: `FILTER_IMPORT_HISTORY_LIMIT`
- actions:
  - undo: `co_filter_import_undo` (`Undo Import`)
  - redo: `co_filter_import_redo` (`Redo Import`)
- audit UI:
  - audit container: `co_filter_import_audit`
  - audit row key pattern: `co_filter_import_audit_row_<idx>`
  - rows include timestamp, kind (`import|undo|redo`), mode, selected/add/changed/removed counts
- status outputs:
  - import apply status includes `+added/~changed/-removed`
  - redo restore status: `redo restored snapshot (...)`
  - depth hint: `undo/redo depth: <u>/<r>`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8163 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8143
curl -s "http://127.0.0.1:8143/frontend/graph_lab/panels.mjs" | rg -n "buildFilterPresetStateSnapshot|compactNameList|filterImportUndoStack|filterImportRedoStack|filterImportAuditTrail|redoLastFilterImport|co_filter_import_undo|co_filter_import_redo|co_filter_import_audit|co_filter_import_audit_row_|undo/redo depth|redo restored snapshot|kind: \"import\"|kind: \"undo\"|kind: \"redo\""
```

Pass criteria:

1. audit + multi-stack history tokens are present
2. undo/redo/audit UI tokens are present
3. backend regression remains pass
