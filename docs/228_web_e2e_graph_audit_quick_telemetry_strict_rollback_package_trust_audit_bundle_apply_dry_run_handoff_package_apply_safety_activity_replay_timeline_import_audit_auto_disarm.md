# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Audit Auto-Disarm (M17.93)

## Goal

Add auto-disarm timer for replay timeline import-confirm-trail replace-confirm safety gate.

1. arm a short-lived replace-confirm window after operator enables import-confirm trail overwrite confirm
2. auto-disarm confirm once timer expires and surface remaining countdown to operator
3. keep status feedback explicit when confirm is armed, disarmed, or auto-disarmed

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline-import audit auto-disarm controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay timeline import-audit auto-disarm tokens:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_IMPORT_CONFIRM_TIMEOUT_MS`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmArmedAtMs`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmTickMs`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportConfirmCountdownHint`
- replay timeline import-audit auto-disarm status string:
  - `dry-run handoff apply confirm activity replay trail import confirm trail import confirm auto-disarmed: re-check confirm to apply import confirm trail`
- replay timeline import-audit auto-disarm UI key:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_confirm_countdown_hint`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import-audit-auto-disarm token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_auto_disarm.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. import-confirm trail replace-confirm timer state + countdown tokens exist
2. auto-disarm status and countdown UI key exist
3. API regression suite remains pass
