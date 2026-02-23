# Web E2E Graph Audit Quick Telemetry + Guided Reset Hint (M17.44)

## Goal

Improve operator observability and reset safety in audit deep-link operations.

1. record quick-apply execution telemetry with scope/result context
2. provide quick telemetry export/copy hooks for operator handoff
3. guide safe reset flow with timeout-based arm hinting

Implementation:

- quick telemetry + guided reset hint:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- quick apply telemetry:
  - constants/helpers:
    - `FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_LIMIT`
    - `normalizeFilterImportAuditQuickApplyTelemetryEntry`
    - `buildFilterImportAuditQuickApplyTelemetryBundle`
    - `serializeFilterImportAuditQuickApplyTelemetryBundle`
  - state/summary:
    - `filterImportAuditQuickApplyTelemetry`
    - `filterImportAuditQuickApplyTelemetrySummary`
  - UI keys:
    - `co_filter_import_audit_quick_telemetry_controls`
    - `co_filter_import_audit_quick_telemetry_copy`
    - `co_filter_import_audit_quick_telemetry_export`
    - `co_filter_import_audit_quick_telemetry_clear`
    - `co_filter_import_audit_quick_telemetry_summary`
  - telemetry captures option id, scope toggles, apply result, sync flags, and preset context
- guided reset safety hint:
  - constants/hints:
    - `FILTER_IMPORT_AUDIT_RESET_ARM_TIMEOUT_MS`
    - `filterImportAuditResetGuidedHint`
  - UI key:
    - `co_filter_import_audit_reset_guided_hint`
  - arm behavior:
    - arming emits explicit status (`reset armed: choose reset action within 20s`)
    - arm auto-expires with explicit status (`reset arm expired: re-arm to execute reset`)

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
curl -s "http://127.0.0.1:8171/frontend/graph_lab/panels.mjs" | rg -n "FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_LIMIT|FILTER_IMPORT_AUDIT_RESET_ARM_TIMEOUT_MS|normalizeFilterImportAuditQuickApplyTelemetryEntry|buildFilterImportAuditQuickApplyTelemetryBundle|serializeFilterImportAuditQuickApplyTelemetryBundle|filterImportAuditQuickApplyTelemetry|filterImportAuditQuickApplyTelemetrySummary|filterImportAuditResetGuidedHint|co_filter_import_audit_quick_telemetry_controls|co_filter_import_audit_quick_telemetry_copy|co_filter_import_audit_quick_telemetry_export|co_filter_import_audit_quick_telemetry_clear|co_filter_import_audit_quick_telemetry_summary|copyFilterImportAuditQuickApplyTelemetryJson|exportFilterImportAuditQuickApplyTelemetryJson|clearFilterImportAuditQuickApplyTelemetry|co_filter_import_audit_reset_guided_hint|reset arm expired: re-arm to execute reset|reset armed: choose reset action within 20s|quick-telemetry total:"
```

Pass criteria:

1. backend regression remains pass
2. quick telemetry tokens are present
3. guided reset hint tokens are present
4. quick telemetry export/copy hooks are present
