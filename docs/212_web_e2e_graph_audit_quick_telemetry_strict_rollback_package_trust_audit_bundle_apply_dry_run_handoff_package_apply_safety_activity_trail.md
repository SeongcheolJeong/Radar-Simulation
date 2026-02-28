# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Trail (M17.77)

## Goal

Add dry-run handoff hydrate-confirm safety activity trail with operator-facing timeline hint.

1. record bounded confirm arm/disarm events for dry-run handoff hydrate safety flow
2. surface concise activity hint with latest event summary and capacity usage
3. expose multiline activity preview so operators can audit confirm behavior locally

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity trail controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- activity trail tokens:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_LIMIT`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrail`
  - `appendQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityEvent`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrailHint`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrailPreview`
- event IDs recorded by flow:
  - `arm_manual`
  - `disarm_manual`
  - `auto_disarm_timeout`
  - `disarm_risk_cleared`
  - `disarm_payload_edit`
  - `disarm_after_hydrate`
  - `disarm_after_reset`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_preview`

## Validation

Trust-audit apply dry-run handoff activity-trail token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_trail.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. activity trail state/helper/hint/preview tokens exist
2. required arm/disarm event IDs and activity UI keys exist
3. API regression suite remains pass
