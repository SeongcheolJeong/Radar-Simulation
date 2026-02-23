# Web E2E Graph Audit Quick Telemetry Drilldown Controls (M17.46)

## Goal

Add failure-centric telemetry drilldown so operators can isolate quick-apply issues without exporting raw JSON first.

1. support failures-only quick telemetry view
2. support reason keyword focus for telemetry filtering
3. expose reason-frequency chips for rapid triage

Implementation:

- drilldown controls + reason chips:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- constants/state:
  - `FILTER_IMPORT_AUDIT_QUICK_REASON_CHIP_LIMIT`
  - `FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX`
  - `filterImportAuditQuickTelemetryFailureOnlyChecked`
  - `filterImportAuditQuickTelemetryReasonQuery`
- drilldown derivations:
  - `filterImportAuditQuickTelemetryReasonQueryNormalized`
  - `filterImportAuditQuickTelemetryRowsDrilldown`
  - `filterImportAuditQuickTelemetryReasonChips`
  - `filterImportAuditQuickTelemetryDrilldownSummary`
- reset action:
  - `clearFilterImportAuditQuickTelemetryDrilldown`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_drilldown_controls`
  - `co_filter_import_audit_quick_telemetry_drilldown_failure_only`
  - `co_filter_import_audit_quick_telemetry_drilldown_reason_query`
  - `co_filter_import_audit_quick_telemetry_drilldown_clear`
  - `co_filter_import_audit_quick_telemetry_drilldown_summary`
  - `co_filter_import_audit_quick_telemetry_reason_chips`
  - `co_filter_import_audit_quick_telemetry_reason_chip_`
  - `co_filter_import_audit_quick_telemetry_reason_chip_empty`
- reset-all preset behavior:
  - clears drilldown toggles/query with other operator context resets

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
curl -s "http://127.0.0.1:8171/frontend/graph_lab/panels.mjs" | rg -n "FILTER_IMPORT_AUDIT_QUICK_REASON_CHIP_LIMIT|FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX|filterImportAuditQuickTelemetryFailureOnlyChecked|filterImportAuditQuickTelemetryReasonQueryNormalized|filterImportAuditQuickTelemetryRowsDrilldown|filterImportAuditQuickTelemetryReasonChips|filterImportAuditQuickTelemetryDrilldownSummary|clearFilterImportAuditQuickTelemetryDrilldown|co_filter_import_audit_quick_telemetry_drilldown_controls|co_filter_import_audit_quick_telemetry_drilldown_failure_only|co_filter_import_audit_quick_telemetry_drilldown_reason_query|co_filter_import_audit_quick_telemetry_drilldown_clear|co_filter_import_audit_quick_telemetry_drilldown_summary|co_filter_import_audit_quick_telemetry_reason_chips|co_filter_import_audit_quick_telemetry_reason_chip_|failures-only|reason focus:|Reset Drilldown|drilldown "
```

Pass criteria:

1. backend regression remains pass
2. drilldown state/derivation tokens are present
3. failure-only/reason-focus UI tokens are present
