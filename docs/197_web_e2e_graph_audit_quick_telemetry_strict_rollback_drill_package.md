# Web E2E Graph Audit Quick Telemetry Strict-Rollback Drill Package (M17.62)

## Goal

Provide a reusable rollback-drill package export containing preset snapshot and checklist report evidence.

1. export/copy strict-rollback drill package JSON
2. include preset snapshot (`preset_id/mode/reason/filter-bundle`) in package payload
3. include checklist report export preview + one-click copy for handoff

Implementation:

- strict-rollback drill package controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- rollback package schema/helpers:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SCHEMA_VERSION`
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_KIND`
  - `buildQuickTelemetryStrictRollbackDrillPackage`
  - `serializeQuickTelemetryStrictRollbackDrillPackage`
- package/report runtime state:
  - `quickTelemetryStrictRollbackDrillPackagePayload`
  - `quickTelemetryDrilldownStrictRollbackChecklistReport`
  - `quickTelemetryDrilldownStrictRollbackChecklistReportPreview`
  - `quickTelemetryDrilldownStrictRollbackPackagePreview`
- package/report actions:
  - `exportQuickTelemetryStrictRollbackDrillPackageToJson`
  - `copyQuickTelemetryStrictRollbackDrillPackageJson`
  - `copyQuickTelemetryStrictRollbackChecklistReportText`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_export`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_copy`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_report_copy`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_report_preview`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_status`

## Validation

Rollback-drill package token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_drill_package.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. rollback package schema/action tokens exist
2. rollback package/checklist report UI tokens exist
3. API regression suite remains pass
