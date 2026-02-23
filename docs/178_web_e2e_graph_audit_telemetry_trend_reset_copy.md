# Web E2E Graph Audit Telemetry Trend Chips + Safe Reset Copy Refinement (M17.45)

## Goal

Improve quick-apply operability after M17.44 by making trend state visible at a glance and making safe-reset intent clearer.

1. expose recent quick-apply trend chips (success/failure/sync/latest reason)
2. refine reset copy to make arm/consume/blocked states explicit
3. add live safe-reset countdown behavior while armed

Implementation:

- telemetry trend chips + reset copy/countdown:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- quick telemetry trend chips:
  - constants/state:
    - `FILTER_IMPORT_AUDIT_QUICK_TREND_WINDOW`
    - `filterImportAuditQuickTelemetryTrend`
  - summary refinement:
    - `filterImportAuditQuickApplyTelemetrySummary` includes `recent:<ok>/<count>`
  - UI keys:
    - `co_filter_import_audit_quick_telemetry_trend_chips`
    - `co_filter_import_audit_quick_telemetry_chip_recent_rate`
    - `co_filter_import_audit_quick_telemetry_chip_fail_streak`
    - `co_filter_import_audit_quick_telemetry_chip_sync_rate`
    - `co_filter_import_audit_quick_telemetry_chip_latest_reason`
- safe reset copy/countdown refinements:
  - armed countdown tick state:
    - `filterImportAuditResetTickMs`
  - guided hint now shows remaining seconds and final-5s urgency copy:
    - `safe reset guide: armed (<Ns left>) ...`
  - refined status copy:
    - arm/disarm:
      - `reset armed: choose reset action within 20s (safe window active)`
      - `reset disarmed: safe reset idle`
    - blocked:
      - `reset blocked: arm reset first (safe window required)`
    - consumed:
      - `audit restore scope reset (safe reset consumed)`
      - `audit pin context reset (safe reset consumed)`
      - `audit operator context reset (safe reset consumed)`

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
curl -s "http://127.0.0.1:8171/frontend/graph_lab/panels.mjs" | rg -n "FILTER_IMPORT_AUDIT_QUICK_TREND_WINDOW|filterImportAuditQuickTelemetryTrend|co_filter_import_audit_quick_telemetry_trend_chips|co_filter_import_audit_quick_telemetry_chip_recent_rate|co_filter_import_audit_quick_telemetry_chip_fail_streak|co_filter_import_audit_quick_telemetry_chip_sync_rate|co_filter_import_audit_quick_telemetry_chip_latest_reason|quick-telemetry total:|safe reset guide: armed \(|reset blocked: arm reset first \(safe window required\)|reset armed: choose reset action within 20s \(safe window active\)|reset disarmed: safe reset idle|audit restore scope reset \(safe reset consumed\)|audit pin context reset \(safe reset consumed\)|audit operator context reset \(safe reset consumed\)"
```

Pass criteria:

1. backend regression remains pass
2. trend chip tokens are present
3. safe-reset countdown/copy refinement tokens are present
