# Web E2E Graph Audit Partial-Restore Toggles + Pin State Chips (M17.40)

## Goal

Make deep-link restore safer by allowing selective scope apply and improve pin-state visibility.

1. allow per-scope restore toggles for deep-link bundle apply
2. prevent accidental full restore when operator wants partial restore
3. surface pin state as compact chips for quick situational awareness

Implementation:

- partial-restore toggles + pin chips:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- partial-restore toggles:
  - state:
    - `filterImportAuditRestoreQueryChecked`
    - `filterImportAuditRestorePagingChecked`
    - `filterImportAuditRestorePinnedPresetChecked`
    - `filterImportAuditRestoreActiveEntryChecked`
  - UI keys:
    - `co_filter_import_audit_restore_scopes`
    - `co_filter_import_audit_restore_query`
    - `co_filter_import_audit_restore_paging`
    - `co_filter_import_audit_restore_pinned`
    - `co_filter_import_audit_restore_entry`
  - apply behavior:
    - `applyFilterImportAuditDeepLinkBundleFromText` applies only enabled scopes
    - no enabled scope returns explicit status: `audit bundle apply skipped: no restore scope enabled`
- pin state chips:
  - container key: `co_filter_import_audit_pin_state_chips`
  - chip keys:
    - `co_filter_import_audit_pin_chip_pinned`
    - `co_filter_import_audit_pin_chip_active`
    - `co_filter_import_audit_pin_chip_custom`
    - `co_filter_import_audit_pin_chip_shortcut`
  - chips reflect pinned id, active/idle status, custom-query status, and shortcut token
- prefs persistence:
  - overlay prefs now include partial-restore toggle states
  - `reset_all` preset restores toggle defaults

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8151 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8171
curl -s "http://127.0.0.1:8151/health"
curl -s "http://127.0.0.1:8171/frontend/graph_lab/panels.mjs" | rg -n "filterImportAuditRestoreQueryChecked|filterImportAuditRestorePagingChecked|filterImportAuditRestorePinnedPresetChecked|filterImportAuditRestoreActiveEntryChecked|co_filter_import_audit_restore_scopes|co_filter_import_audit_restore_query|co_filter_import_audit_restore_paging|co_filter_import_audit_restore_pinned|co_filter_import_audit_restore_entry|co_filter_import_audit_pin_state_chips|co_filter_import_audit_pin_chip_pinned|co_filter_import_audit_pin_chip_active|co_filter_import_audit_pin_chip_custom|co_filter_import_audit_pin_chip_shortcut|audit bundle apply skipped: no restore scope enabled|scope:"
```

Pass criteria:

1. backend regression remains pass
2. partial-restore toggle tokens are present
3. pin-state chip tokens are present
