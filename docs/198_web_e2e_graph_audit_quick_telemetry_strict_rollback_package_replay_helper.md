# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Replay Helper (M17.63)

## Goal

Enable rollback package replay with explicit import preview and checklist delta guard.

1. parse and preview rollback package payload before replay
2. compare imported checklist report vs live checklist and surface delta guard summary
3. block replay on delta unless operator confirms override

Implementation:

- strict-rollback package replay controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- package parse/replay tokens:
  - `parseQuickTelemetryStrictRollbackDrillPackageText`
  - `parsedQuickTelemetryStrictRollbackDrillPackagePayload`
  - `quickTelemetryStrictRollbackPackageChecklistDeltaGuard`
  - `quickTelemetryStrictRollbackPackageChecklistDeltaHint`
  - `quickTelemetryStrictRollbackPackageReplayPreview`
  - `replayQuickTelemetryStrictRollbackPackageFromText`
- replay guard state:
  - `quickTelemetryDrilldownStrictRollbackPackageReplayText`
  - `quickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_replay_preview`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_delta_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_delta_confirm`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_delta_confirm_checkbox`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_replay`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_replay_text`

## Validation

Rollback-package replay helper token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_replay_helper.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. package parse/replay + delta guard tokens exist
2. replay preview/guard UI tokens exist
3. API regression suite remains pass
