# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Audit Trail (M17.88)

## Goal

Add dry-run handoff confirm-activity replay timeline-import replacement-confirm audit trail with operator-facing hint.

1. record bounded timeline-import confirm arm/disarm/auto-disarm timeline events
2. surface concise timeline-import confirm trail hint with latest event summary and capacity usage
3. expose multiline timeline-import confirm trail preview so operators can audit import-confirm behavior locally

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline-import audit trail controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay-timeline-import-audit-trail tokens:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_LIMIT`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail`
  - `appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailHint`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailPreview`
- replay-timeline-import-audit-trail event IDs:
  - `trail_import_arm_manual`
  - `trail_import_disarm_manual`
  - `trail_import_auto_disarm_timeout`
  - `trail_import_disarm_risk_cleared`
  - `trail_import_disarm_payload_edit`
  - `trail_import_disarm_after_apply`
- replay-timeline-import-audit-trail UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_preview`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import-audit-trail token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_trail.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. timeline-import confirm trail state/helper/hint/preview tokens exist
2. timeline-import confirm arm/disarm/auto-disarm event IDs and trail UI keys exist
3. API regression suite remains pass
