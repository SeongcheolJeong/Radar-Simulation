# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Trail (M17.82)

## Goal

Add dry-run handoff confirm-activity replay replacement-confirm timeline trail with operator-facing hint.

1. record bounded replay confirm arm/disarm/auto-disarm timeline events
2. surface concise replay trail hint with latest event summary and capacity usage
3. expose multiline replay trail preview so operators can audit replay-confirm behavior locally

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline trail controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay trail tokens:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_LIMIT`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrail`
  - `appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmEvent`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailHint`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailPreview`
- replay trail event IDs:
  - `replay_arm_manual`
  - `replay_disarm_manual`
  - `replay_auto_disarm_timeout`
  - `replay_disarm_risk_cleared`
  - `replay_disarm_payload_edit`
  - `replay_disarm_after_replay`
- replay trail UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_preview`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-trail token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_trail.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. replay timeline trail state/helper/hint/preview tokens exist
2. replay arm/disarm/auto-disarm event IDs and trail UI keys exist
3. API regression suite remains pass
