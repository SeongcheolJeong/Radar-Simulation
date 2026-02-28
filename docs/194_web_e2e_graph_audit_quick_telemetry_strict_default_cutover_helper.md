# Web E2E Graph Audit Quick Telemetry Strict-Default Cutover Helper (M17.59)

## Goal

Provide operator actions to switch strict mode to default safely, with explicit compat fallback reminders.

1. one-click `Apply Strict Default` helper
2. one-click `Switch to Compat Fallback` helper
3. cutover hint/reminder/status surface near adoption gate panel

Implementation:

- strict-default cutover helper controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- cutover helper state/derived hints:
  - `quickTelemetryDrilldownStrictCutoverStatus`
  - `quickTelemetryDrilldownStrictCutoverHint`
  - `quickTelemetryDrilldownCompatFallbackReminder`
- helper actions:
  - `applyQuickTelemetryStrictDefaultCutoverPreset`
  - `switchQuickTelemetryToCompatFallback`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_apply`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_compat`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_reminder`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_status`

## Validation

Cutover-helper token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_cutover_helper.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. strict-default and compat-fallback helper tokens exist
2. cutover hint/reminder/status tokens exist
3. API regression suite remains pass
