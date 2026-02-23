# Web E2E Graph Audit Restore Presets + Pin Chip Filter Controls (M17.41)

## Goal

Speed up deep-link restore operations and reduce visual noise in audit pin-state chips.

1. add one-click restore preset shortcuts for common partial-restore combinations
2. keep restore scope toggles and restore apply behavior consistent
3. add pin-chip visibility filter controls for operator-focused views

Implementation:

- restore presets + pin chip filter controls:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- restore preset shortcuts:
  - constants/helpers:
    - `FILTER_IMPORT_AUDIT_RESTORE_PRESETS`
    - `resolveFilterImportAuditRestorePreset`
    - `activeFilterImportAuditRestorePresetId`
    - `applyFilterImportAuditRestorePreset`
  - UI keys:
    - `co_filter_import_audit_restore_presets`
    - `co_filter_import_audit_restore_preset_all`
    - `co_filter_import_audit_restore_preset_query_pin`
    - `co_filter_import_audit_restore_preset_paging_entry`
    - `co_filter_import_audit_restore_preset_query_only`
    - `co_filter_import_audit_restore_preset_active`
  - apply status includes restore tag:
    - `audit deep-link bundle applied (..., restore:<preset|custom>)`
- pin chip filter controls:
  - constants/helpers:
    - `FILTER_IMPORT_AUDIT_PIN_CHIP_FILTER_OPTIONS`
    - `normalizeFilterImportAuditPinChipFilter`
    - `filterImportAuditPinChipVisibility`
  - state/prefs:
    - `filterImportAuditPinChipFilter`
    - persisted in overlay prefs and restored by `reset_all`
  - UI keys:
    - `co_filter_import_audit_pin_chip_filters`
    - `co_filter_import_audit_pin_chip_filter_all`
    - `co_filter_import_audit_pin_chip_filter_state`
    - `co_filter_import_audit_pin_chip_filter_context`
    - `co_filter_import_audit_pin_chip_filter_shortcut`
    - `co_filter_import_audit_pin_chip_filter_active`

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
curl -s "http://127.0.0.1:8171/frontend/graph_lab/panels.mjs" | rg -n "FILTER_IMPORT_AUDIT_RESTORE_PRESETS|FILTER_IMPORT_AUDIT_PIN_CHIP_FILTER_OPTIONS|resolveFilterImportAuditRestorePreset|normalizeFilterImportAuditPinChipFilter|filterImportAuditPinChipFilter|activeFilterImportAuditRestorePresetId|filterImportAuditPinChipVisibility|co_filter_import_audit_restore_presets|co_filter_import_audit_restore_preset_all|co_filter_import_audit_restore_preset_query_pin|co_filter_import_audit_restore_preset_paging_entry|co_filter_import_audit_restore_preset_query_only|co_filter_import_audit_restore_preset_active|co_filter_import_audit_pin_chip_filters|co_filter_import_audit_pin_chip_filter_all|co_filter_import_audit_pin_chip_filter_state|co_filter_import_audit_pin_chip_filter_context|co_filter_import_audit_pin_chip_filter_shortcut|co_filter_import_audit_pin_chip_filter_active|audit restore preset:|restore:"
```

Pass criteria:

1. backend regression remains pass
2. restore preset tokens are present
3. pin chip filter tokens are present
4. deep-link apply status includes restore tag
