# Web E2E Graph Audit Quick Telemetry Import Filter-Bundle Transfer (M17.54)

## Goal

Enable team handoff for drilldown import filter state via explicit copy/export/import flow.

1. add JSON serialization/parsing for import filter bundle
2. add filter-bundle transfer controls (export/copy/import) with payload preview
3. keep apply target scoped to filter controls (`conflict_only/conflict_filter/name_query/row_cap`)

Implementation:

- transfer helper + UI:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- helper contract:
  - `buildQuickTelemetryDrilldownImportFilterBundle`
  - `serializeQuickTelemetryDrilldownImportFilterBundle`
  - `parseQuickTelemetryDrilldownImportFilterBundleText`
- transfer state:
  - `quickTelemetryDrilldownImportFilterBundleText`
  - `quickTelemetryDrilldownImportFilterBundleStatus`
  - `parsedQuickTelemetryDrilldownImportFilterBundlePayload`
  - `quickTelemetryDrilldownImportFilterBundlePreview`
- transfer actions:
  - `exportQuickTelemetryDrilldownImportFilterBundleToJson`
  - `copyQuickTelemetryDrilldownImportFilterBundleJson`
  - `importQuickTelemetryDrilldownImportFilterBundleFromText`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_transfer`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_export`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_copy`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_import`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_preview`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_text`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_status`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend token contract smoke:

```bash
rg -n "buildQuickTelemetryDrilldownImportFilterBundle|serializeQuickTelemetryDrilldownImportFilterBundle|parseQuickTelemetryDrilldownImportFilterBundleText|quickTelemetryDrilldownImportFilterBundleText|quickTelemetryDrilldownImportFilterBundleStatus|parsedQuickTelemetryDrilldownImportFilterBundlePayload|quickTelemetryDrilldownImportFilterBundlePreview|exportQuickTelemetryDrilldownImportFilterBundleToJson|copyQuickTelemetryDrilldownImportFilterBundleJson|importQuickTelemetryDrilldownImportFilterBundleFromText|co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_transfer|co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_export|co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_copy|co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_import|co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_text|co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_status|co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_preview" /Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs
```

Pass criteria:

1. backend regression remains pass
2. filter-bundle serialize/parse/apply tokens are present
3. transfer UI + preview/status tokens are present
