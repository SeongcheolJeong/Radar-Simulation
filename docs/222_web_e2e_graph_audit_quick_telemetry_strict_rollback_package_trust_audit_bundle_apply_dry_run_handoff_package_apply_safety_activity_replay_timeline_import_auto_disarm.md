# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Auto-Disarm (M17.87)

## Goal

Add bounded auto-disarm safety for dry-run handoff confirm-activity replay timeline import replacement-confirm.

1. arm replay timeline-import replacement-confirm with a strict timeout window (`20s`)
2. auto-disarm replay timeline-import replacement-confirm when timeout expires
3. surface replay timeline-import confirm countdown hint near import controls for operator clarity

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline-import auto-disarm controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay-timeline-import-auto-disarm tokens:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TIMEOUT_MS`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmCountdownHint`
- replay-timeline-import-auto-disarm status strings:
  - `dry-run handoff apply confirm activity replay trail import confirm armed (within 20s or it auto-disarms)`
  - `dry-run handoff apply confirm activity replay trail import confirm auto-disarmed: re-check confirm to import replay timeline`
  - `dry-run handoff apply confirm activity replay trail import confirm disarmed`
- replay-timeline-import-auto-disarm UI key:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_countdown_hint`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import auto-disarm token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_auto_disarm.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. replay timeline-import confirm timer/countdown token paths exist
2. replay timeline-import confirm arm/disarm/auto-disarm status + countdown UI token exists
3. API regression suite remains pass
