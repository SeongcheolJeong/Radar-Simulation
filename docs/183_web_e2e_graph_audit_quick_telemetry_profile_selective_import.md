# Web E2E Graph Audit Quick Telemetry Profile Selective Import + Conflict-Only View (M17.50)

## Goal

Extend drilldown profile transfer so operators can import only selected profiles and optionally focus on overwrite conflicts.

1. add per-profile selection toggles for import payload rows
2. add conflict-only view filter for row inspection/import scope
3. keep M17.49 guardrails (overwrite confirm + rollback snapshot) with selected-row semantics

Implementation:

- selective import logic + UI:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- selection/filter state:
  - `quickTelemetryDrilldownImportSelection`
  - `quickTelemetryDrilldownImportConflictOnlyChecked`
- row derivation + selected scope:
  - `quickTelemetryDrilldownImportRowsVisible`
  - `quickTelemetryDrilldownImportSelectionRows`
  - `selectedQuickTelemetryDrilldownImportNames`
  - `selectedQuickTelemetryDrilldownImportRows`
- selection actions:
  - `toggleQuickTelemetryDrilldownImportSelection`
  - `selectAllQuickTelemetryDrilldownImportRowsVisible`
  - `clearQuickTelemetryDrilldownImportSelection`
- import semantics:
  - `importQuickTelemetryDrilldownProfilesFromText` imports only selected rows
  - overwrite confirm gate applies only to selected changed-overwrite rows
  - `import skipped: select profiles` status on empty selection
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_conflict_only`
  - `co_filter_import_audit_quick_telemetry_profile_import_select_all`
  - `co_filter_import_audit_quick_telemetry_profile_import_select_none`
  - `co_filter_import_audit_quick_telemetry_profile_import_rows`
  - `co_filter_import_audit_quick_telemetry_profile_import_rows_empty`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend token contract smoke:

```bash
rg -n "quickTelemetryDrilldownImportSelection|quickTelemetryDrilldownImportConflictOnlyChecked|quickTelemetryDrilldownImportRowsVisible|quickTelemetryDrilldownImportSelectionRows|selectedQuickTelemetryDrilldownImportNames|toggleQuickTelemetryDrilldownImportSelection|selectAllQuickTelemetryDrilldownImportRowsVisible|clearQuickTelemetryDrilldownImportSelection|import skipped: select profiles|co_filter_import_audit_quick_telemetry_profile_import_conflict_only|co_filter_import_audit_quick_telemetry_profile_import_select_all|co_filter_import_audit_quick_telemetry_profile_import_select_none|co_filter_import_audit_quick_telemetry_profile_import_rows|import rows: no matches in current view" /Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs
```

Pass criteria:

1. backend regression remains pass
2. selection/conflict-only derivation and handlers are present
3. import status/UI contract tokens for selected-scope import are present
