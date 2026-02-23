# Web E2E Graph Audit Quick Telemetry Profile Import Pagination + Selection Safety (M17.51)

## Goal

Harden large-payload drilldown profile import UX with explicit page navigation and selection safety visibility.

1. add rows/page cap + window navigation for import preview rows
2. support page-scoped selection actions in addition to scope-wide selection
3. expose selection safety hints (off-page selection + hidden-by-view selection)

Implementation:

- pagination/safety logic + UI:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- state/prefs:
  - `quickTelemetryDrilldownImportRowCapText`
  - `quickTelemetryDrilldownImportRowOffset`
  - `quickTelemetryDrilldownImportRowCap`
  - `quickTelemetryDrilldownImportMaxOffset`
  - `quickTelemetryDrilldownImportRowEnd`
  - `quickTelemetryDrilldownImportRowsPage`
  - persisted prefs:
    - `quickTelemetryDrilldownImportConflictOnly`
    - `quickTelemetryDrilldownImportRowCap`
- selection safety:
  - `quickTelemetryDrilldownImportSelectedOffPageCount`
  - `quickTelemetryDrilldownImportHiddenSelectionCount`
  - `quickTelemetryDrilldownImportSelectionSafetyHint`
- page actions:
  - `selectPageQuickTelemetryDrilldownImportSelection`
  - `clearPageQuickTelemetryDrilldownImportSelection`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_row_cap`
  - `co_filter_import_audit_quick_telemetry_profile_import_page_top`
  - `co_filter_import_audit_quick_telemetry_profile_import_page_prev`
  - `co_filter_import_audit_quick_telemetry_profile_import_page_next`
  - `co_filter_import_audit_quick_telemetry_profile_import_select_page`
  - `co_filter_import_audit_quick_telemetry_profile_import_clear_page`
  - `co_filter_import_audit_quick_telemetry_profile_import_page_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_selection_safety`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend token contract smoke:

```bash
rg -n "QUICK_TELEMETRY_DRILLDOWN_IMPORT_ROW_CAP_OPTIONS|quickTelemetryDrilldownImportRowCapText|quickTelemetryDrilldownImportRowCap|quickTelemetryDrilldownImportRowOffset|quickTelemetryDrilldownImportMaxOffset|quickTelemetryDrilldownImportRowEnd|quickTelemetryDrilldownImportRowsPage|quickTelemetryDrilldownImportSelectionSafetyHint|quickTelemetryDrilldownImportSelectedOffPageCount|quickTelemetryDrilldownImportHiddenSelectionCount|selectPageQuickTelemetryDrilldownImportSelection|clearPageQuickTelemetryDrilldownImportSelection|co_filter_import_audit_quick_telemetry_profile_import_row_cap|co_filter_import_audit_quick_telemetry_profile_import_page_top|co_filter_import_audit_quick_telemetry_profile_import_page_prev|co_filter_import_audit_quick_telemetry_profile_import_page_next|co_filter_import_audit_quick_telemetry_profile_import_select_page|co_filter_import_audit_quick_telemetry_profile_import_clear_page|co_filter_import_audit_quick_telemetry_profile_import_selection_safety|co_filter_import_audit_quick_telemetry_profile_import_page_hint" /Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs
```

Pass criteria:

1. backend regression remains pass
2. pagination/window derivation + page actions exist
3. selection safety hint tokens exist and are wired into transfer panel UI
