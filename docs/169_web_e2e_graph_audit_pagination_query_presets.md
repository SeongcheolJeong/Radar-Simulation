# Web E2E Graph Audit Pagination Cap + Query Preset Shortcuts (M17.36)

## Goal

Keep import-audit browsing stable when history grows while speeding up common query actions.

1. add bounded audit row pagination controls
2. add one-click audit query presets
3. keep audit detail selection coherent with current page window

Implementation:

- audit pagination + query presets:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- query preset shortcuts:
  - presets: `FILTER_IMPORT_AUDIT_QUERY_PRESETS`
  - active preset detector: `activeFilterImportAuditQueryPresetId`
  - apply callback: `applyFilterImportAuditQueryPreset`
  - UI keys: `co_filter_import_audit_preset_<preset_id>`
- pagination cap:
  - cap options: `FILTER_IMPORT_AUDIT_ROW_CAP_OPTIONS`
  - state:
    - `filterImportAuditRowCapText`
    - `filterImportAuditRowOffset`
  - computed:
    - `filterImportAuditRowsVisible`
    - `filterImportAuditMaxOffset`
    - `filterImportAuditRowEnd`
  - UI keys:
    - `co_filter_import_audit_row_cap`
    - `co_filter_import_audit_top`
    - `co_filter_import_audit_prev`
    - `co_filter_import_audit_next`
    - `co_filter_import_audit_window_hint`
- persistence:
  - overlay prefs include `filterImportAuditRowCap`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8147 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8167
curl -s "http://127.0.0.1:8147/health"
curl -s "http://127.0.0.1:8167/frontend/graph_lab/panels.mjs" | rg -n "FILTER_IMPORT_AUDIT_ROW_CAP_OPTIONS|FILTER_IMPORT_AUDIT_QUERY_PRESETS|filterImportAuditRowCapText|filterImportAuditRowOffset|filterImportAuditRowsVisible|filterImportAuditMaxOffset|filterImportAuditRowEnd|activeFilterImportAuditQueryPresetId|applyFilterImportAuditQueryPreset|co_filter_import_audit_preset_|co_filter_import_audit_row_cap|co_filter_import_audit_window_hint|co_filter_import_audit_top|co_filter_import_audit_prev|co_filter_import_audit_next"
```

Pass criteria:

1. backend regression remains pass
2. audit pagination cap controls/tokens are present
3. audit query preset controls/tokens are present
