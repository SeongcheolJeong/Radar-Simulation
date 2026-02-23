# Web E2E Graph Audit Reset UX + Row-Volume Guardrails (M17.35)

## Goal

Improve operability for long contract timelines without changing backend semantics.

1. add one-click reset for audit query controls
2. add row-volume guardrails for large filtered result sets
3. allow explicit operator bypass with visible status

Implementation:

- audit reset + row-volume guardrails:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- audit query reset:
  - callback: `resetFilterImportAuditQuery`
  - UI key: `co_filter_import_audit_reset`
  - reset target:
    - `filterImportAuditSearchText -> ""`
    - `filterImportAuditKindFilter -> "all"`
    - `filterImportAuditModeFilter -> "all"`
- row-volume guardrails:
  - constants:
    - `CONTRACT_ROW_VOLUME_GUARD_TRIGGER`
    - `CONTRACT_ROW_VOLUME_GUARD_MAX_WINDOW`
    - `ROW_WINDOW_SIZE_OPTIONS`
  - computed state:
    - `rowVolumeGuardActive`
    - `rowWindowOptionValues`
  - active guard behavior:
    - when `rowVolumeGuardActive && !rowVolumeGuardBypass`, `rows/window` options are capped at safe max
    - existing oversized `rowWindowSizeText` is clamped to safe max
- operator override + visibility:
  - state: `rowVolumeGuardBypass`
  - UI key: `co_row_volume_guard_bypass`
  - hint key: `co_row_volume_guard_hint`
  - active-filter summary token: `rows_guard:off`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8146 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8166
curl -s "http://127.0.0.1:8146/health"
curl -s "http://127.0.0.1:8166/frontend/graph_lab/panels.mjs" | rg -n "CONTRACT_ROW_VOLUME_GUARD_TRIGGER|CONTRACT_ROW_VOLUME_GUARD_MAX_WINDOW|rowVolumeGuardBypass|rowVolumeGuardActive|rowWindowOptionValues|co_row_volume_guard_bypass|co_row_volume_guard_hint|rows_guard:off|resetFilterImportAuditQuery|filterImportAuditQueryActive|co_filter_import_audit_reset"
```

Pass criteria:

1. backend regression remains pass
2. row-volume guard tokens are present in frontend module
3. audit query reset tokens are present in frontend module
