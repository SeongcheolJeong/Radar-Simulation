# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Audit Safety Refresh (M17.98)

## Goal

Refresh import-confirm safety handling so controls status remains continuous through confirm arm/disarm transitions.

1. align controls-status output with manual arm/disarm, payload-edit disarm, risk-clear disarm, and auto-disarm timeout
2. keep safety lifecycle status visible through the existing import-confirm controls hint path
3. preserve existing safety checks/timers while adding additive controls-status continuity

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline-import audit safety refresh:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay timeline import-audit safety refresh tokens:
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportSafety`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmChecked`
- replay timeline import-audit safety refresh status strings:
  - `import confirm trail controls: replacement confirm armed`
  - `import confirm trail controls: replacement confirm disarmed (manual)`
  - `import confirm trail controls: replacement confirm disarmed (payload edit)`
  - `import confirm trail controls: replacement confirm disarmed (risk cleared)`
  - `import confirm trail controls: replacement confirm auto-disarmed (timer elapsed)`
- replay timeline import-audit safety refresh UI key:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_confirm_checkbox`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import-audit-safety-refresh token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_safety_refresh.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. safety-refresh state + confirm-checkbox tokens exist
2. safety lifecycle controls-status strings exist
3. API regression suite remains pass
