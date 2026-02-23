# Web E2E Graph Audit Quick Telemetry Profile Import Query/Filter Aids (M17.52)

## Goal

Improve drilldown profile import triage speed with name-based search and conflict-class filter chips.

1. add profile-name contains query filter for import rows
2. add conflict-class chips with scoped counts (`all/new/overwrite/changed/same/builtin/custom`)
3. keep selection/import semantics aligned to active filtered view and preserve safety hints

Implementation:

- query/filter derivation + UI:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- state/prefs:
  - `quickTelemetryDrilldownImportNameQuery`
  - `quickTelemetryDrilldownImportConflictFilter`
  - persisted prefs:
    - `quickTelemetryDrilldownImportNameQuery`
    - `quickTelemetryDrilldownImportConflictFilter`
- filter model:
  - `QUICK_TELEMETRY_DRILLDOWN_IMPORT_NAME_QUERY_MAX`
  - `QUICK_TELEMETRY_DRILLDOWN_IMPORT_CONFLICT_FILTER_OPTIONS`
  - `normalizeQuickTelemetryDrilldownImportConflictFilter`
  - `matchQuickTelemetryDrilldownImportConflictFilter`
  - `quickTelemetryDrilldownImportRowsByQuery`
  - `quickTelemetryDrilldownImportConflictFilterCounts`
- import view/selection scope:
  - `quickTelemetryDrilldownImportRowsVisible`
  - `quickTelemetryDrilldownImportSelectionRows`
  - preview/safety text includes active filter/query tokens
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_name_query`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_reset`
  - `co_filter_import_audit_quick_telemetry_profile_import_conflict_filter_chips`
  - `co_filter_import_audit_quick_telemetry_profile_import_conflict_filter_chip_`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend token contract smoke:

```bash
rg -n "QUICK_TELEMETRY_DRILLDOWN_IMPORT_NAME_QUERY_MAX|QUICK_TELEMETRY_DRILLDOWN_IMPORT_CONFLICT_FILTER_OPTIONS|normalizeQuickTelemetryDrilldownImportConflictFilter|matchQuickTelemetryDrilldownImportConflictFilter|quickTelemetryDrilldownImportNameQuery|quickTelemetryDrilldownImportConflictFilter|quickTelemetryDrilldownImportRowsByQuery|quickTelemetryDrilldownImportConflictFilterCounts|co_filter_import_audit_quick_telemetry_profile_import_name_query|co_filter_import_audit_quick_telemetry_profile_import_filter_reset|co_filter_import_audit_quick_telemetry_profile_import_conflict_filter_chips|co_filter_import_audit_quick_telemetry_profile_import_conflict_filter_chip_" /Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs
```

Pass criteria:

1. backend regression remains pass
2. name-query/conflict-filter derivation and normalization tokens are present
3. query input + conflict chip UI tokens are present
