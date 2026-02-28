# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Audit Controls (M17.89)

## Goal

Add replay timeline-import replace-confirm audit controls for dry-run handoff confirm-activity replay flow.

1. provide explicit timeline-import confirm-trail reset control for operator cleanup
2. provide timeline-import confirm-trail copy/export controls for audit handoff transfer
3. keep timeline-import confirm-trail payload bounded and schema/kind tagged for reproducible transfer

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline-import audit controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay-timeline-import-audit-control bundle tokens:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_SCHEMA_VERSION`
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TRAIL_KIND`
  - `buildQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailBundle`
  - `serializeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailBundle`
- replay-timeline-import-audit-control callbacks:
  - `copyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailJson`
  - `exportQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailToJson`
  - `resetQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail`
- replay-timeline-import-audit-control UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_copy`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_export`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_reset`
- replay-timeline-import-audit-control status strings:
  - `dry-run handoff apply confirm activity replay trail import confirm trail copied (`
  - `dry-run handoff apply confirm activity replay trail import confirm trail export complete (`
  - `dry-run handoff apply confirm activity replay trail import confirm trail reset`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import-audit-controls token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_controls.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. timeline-import confirm-trail schema/kind + serializer tokens exist
2. timeline-import confirm-trail copy/export/reset callbacks and UI keys exist
3. API regression suite remains pass
