# Web E2E Graph Audit Quick Telemetry Strict-Cutover Timeline Ledger (M17.60)

## Goal

Add strict-cutover timeline evidence rows for apply/fallback actions, with export/copy/reset controls and status trail.

1. log `Apply Strict Default` / `Switch to Compat Fallback` events
2. surface timeline hint + preview rows near cutover helper controls
3. provide timeline export/copy/reset controls with explicit status messages

Implementation:

- strict-cutover timeline ledger controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- timeline ledger constants/bundle schema:
  - `QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_LIMIT`
  - `QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_SCHEMA_VERSION`
  - `QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_KIND`
  - `normalizeQuickTelemetryDrilldownStrictCutoverLedgerEntry`
  - `buildQuickTelemetryDrilldownStrictCutoverLedgerBundle`
  - `serializeQuickTelemetryDrilldownStrictCutoverLedgerBundle`
- timeline actions:
  - `appendQuickTelemetryDrilldownStrictCutoverLedgerEvent`
  - `exportQuickTelemetryDrilldownStrictCutoverLedgerToJson`
  - `copyQuickTelemetryDrilldownStrictCutoverLedgerJson`
  - `resetQuickTelemetryDrilldownStrictCutoverLedger`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_export`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_copy`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_reset`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_preview`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_status`

## Validation

Timeline-ledger token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_cutover_timeline.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. strict-cutover timeline tokens exist
2. timeline export/copy/reset UI tokens exist
3. API regression suite remains pass
