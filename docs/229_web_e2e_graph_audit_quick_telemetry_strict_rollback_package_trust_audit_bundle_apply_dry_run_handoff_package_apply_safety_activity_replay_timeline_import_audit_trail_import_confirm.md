# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Audit Trail Import Confirm (M17.94)

## Goal

Add import-confirm safety lifecycle events to replay timeline import-audit trail.

1. log manual arm/disarm events when operator toggles import-confirm replace-confirm checkbox
2. log payload-edit disarm, risk-clear disarm, auto-disarm timeout, and apply-time disarm transitions
3. keep operator hint context attached to trail details for quick audit interpretation

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline-import audit trail import-confirm events:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay timeline import-audit trail import-confirm tokens:
  - `appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmEvent`
  - `import_confirm_trail_import_arm_manual`
  - `import_confirm_trail_import_disarm_manual`
  - `import_confirm_trail_import_disarm_payload_edit`
  - `import_confirm_trail_import_disarm_risk_cleared`
  - `import_confirm_trail_import_auto_disarm_timeout`
  - `import_confirm_trail_import_disarm_after_apply`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportOperatorHint`
- replay timeline import-audit trail UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_preview`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import-audit-trail-import-confirm token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_trail_import_confirm.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. import-confirm trail arm/disarm/timeout/apply event tokens exist
2. operator-hint-linked trail detail token and trail UI keys exist
3. API regression suite remains pass
