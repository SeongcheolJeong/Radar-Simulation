# Web E2E Graph Audit Quick Telemetry Drilldown Presets + Handoff Bundle (M17.47)

## Goal

Make quick telemetry drilldown reusable and handoff-ready for operators.

1. add drilldown preset buttons for failure/reason triage
2. export/copy drilldown-filtered telemetry as a dedicated JSON bundle
3. make reason chips actionable for one-click focus

Implementation:

- drilldown preset/handoff flow:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- new constants/helpers:
  - `FILTER_IMPORT_AUDIT_QUICK_DRILLDOWN_PRESETS`
  - `resolveFilterImportAuditQuickDrilldownPreset`
  - `buildFilterImportAuditQuickTelemetryDrilldownBundle`
  - `serializeFilterImportAuditQuickTelemetryDrilldownBundle`
- new drilldown state/derived id:
  - `activeFilterImportAuditQuickTelemetryDrilldownPresetId`
- new actions:
  - `applyFilterImportAuditQuickTelemetryDrilldownPreset`
  - `copyFilterImportAuditQuickTelemetryDrilldownJson`
  - `exportFilterImportAuditQuickTelemetryDrilldownJson`
  - `applyFilterImportAuditQuickTelemetryReasonChip`
- dedicated handoff bundle kind:
  - `graph_lab_contract_overlay_filter_import_quick_apply_telemetry_drilldown`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_drilldown_presets`
  - `co_filter_import_audit_quick_telemetry_drilldown_preset_`
  - `co_filter_import_audit_quick_telemetry_drilldown_copy`
  - `co_filter_import_audit_quick_telemetry_drilldown_export`
  - `co_filter_import_audit_quick_telemetry_drilldown_preset_active`

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
curl -s "http://127.0.0.1:8171/frontend/graph_lab/panels.mjs" | rg -n "FILTER_IMPORT_AUDIT_QUICK_DRILLDOWN_PRESETS|resolveFilterImportAuditQuickDrilldownPreset|buildFilterImportAuditQuickTelemetryDrilldownBundle|serializeFilterImportAuditQuickTelemetryDrilldownBundle|activeFilterImportAuditQuickTelemetryDrilldownPresetId|applyFilterImportAuditQuickTelemetryDrilldownPreset|copyFilterImportAuditQuickTelemetryDrilldownJson|exportFilterImportAuditQuickTelemetryDrilldownJson|applyFilterImportAuditQuickTelemetryReasonChip|co_filter_import_audit_quick_telemetry_drilldown_presets|co_filter_import_audit_quick_telemetry_drilldown_preset_|co_filter_import_audit_quick_telemetry_drilldown_copy|co_filter_import_audit_quick_telemetry_drilldown_export|co_filter_import_audit_quick_telemetry_drilldown_preset_active|graph_lab_contract_overlay_filter_import_quick_apply_telemetry_drilldown|Copy Drilldown JSON|Export Drilldown JSON|drilldown preset:"
```

Pass criteria:

1. backend regression remains pass
2. drilldown preset + handoff bundle tokens are present
3. drilldown copy/export operator controls are present
