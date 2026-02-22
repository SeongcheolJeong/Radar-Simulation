# Web E2E Graph Import History Maintenance + Audit Search/Filter (M17.34)

## Goal

Keep filter-import history operable when sessions get long.

1. add explicit history maintenance controls (clear/prune)
2. add audit search/filter controls for targeted evidence lookup
3. keep detail drilldown selection coherent under filtered results

Implementation:

- import-history maintenance + audit filtering:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- history maintenance controls:
  - callbacks:
    - `clearFilterImportHistory`
    - `pruneFilterImportHistory`
  - UI keys:
    - `co_filter_import_prune_keep`
    - `co_filter_import_prune`
    - `co_filter_import_clear`
  - prune bound: `1..FILTER_IMPORT_HISTORY_LIMIT`
- audit query controls:
  - search text key: `co_filter_import_audit_search`
  - kind filter key: `co_filter_import_audit_kind`
  - mode filter key: `co_filter_import_audit_mode`
  - selectable option sets:
    - `FILTER_IMPORT_AUDIT_KIND_OPTIONS`
    - `FILTER_IMPORT_AUDIT_MODE_OPTIONS`
- filtered audit view model:
  - computed rows: `filterImportAuditRowsFiltered`
  - active detail fallback sync on filter-result changes
  - visible count hint key: `co_filter_import_audit_count`
  - no-match hint: `no audit rows matched current filters`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8145 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8165
curl -s "http://127.0.0.1:8145/health"
curl -s "http://127.0.0.1:8165/frontend/graph_lab/panels.mjs" | rg -n "clearFilterImportHistory|pruneFilterImportHistory|filterImportAuditRowsFiltered|co_filter_import_audit_search|co_filter_import_audit_kind|co_filter_import_audit_mode|co_filter_import_prune_keep|co_filter_import_prune|co_filter_import_clear|co_filter_import_audit_count|no audit rows matched current filters"
```

Pass criteria:

1. backend regression remains pass
2. history maintenance controls/tokens are present
3. audit search/filter + filtered-view synchronization tokens are present
