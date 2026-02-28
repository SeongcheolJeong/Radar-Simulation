# Web E2E Graph Audit Quick Telemetry Strict-Rollback Drill Helper (M17.61)

## Goal

Add failure-tagged compat-fallback drill presets and an operator checklist so strict-cutover rollback rehearsals are reproducible.

1. one-click rollback drill presets (`parse_error`, `invalid_payload`, `no_scope`)
2. rollback checklist (`mode/failure-only/reason/failure-row`) with `READY|HOLD` summary
3. rollback status trail tied to cutover helper actions

Implementation:

- strict-rollback drill helper controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- rollback preset/checklist tokens:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PRESETS`
  - `resolveQuickTelemetryStrictRollbackDrillPreset`
  - `activeQuickTelemetryStrictRollbackDrillPresetId`
  - `quickTelemetryDrilldownStrictRollbackChecklist`
  - `quickTelemetryDrilldownStrictRollbackChecklistHint`
  - `quickTelemetryDrilldownStrictRollbackChecklistPreview`
  - `applyQuickTelemetryStrictRollbackDrillPreset`
  - `resetQuickTelemetryStrictRollbackDrillPreset`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_checklist_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_checklist_preview`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_preset_chip_`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_reset`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_status`

## Validation

Rollback-drill helper token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_drill_helper.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. rollback preset/checklist tokens exist
2. rollback helper UI tokens exist
3. API regression suite remains pass
