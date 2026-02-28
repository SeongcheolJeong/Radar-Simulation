# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay (M17.79)

## Goal

Add dry-run handoff hydrate-confirm activity replay path with schema guard and import preview.

1. parse imported confirm-activity bundle with strict kind/schema guard
2. surface import preview/guidance so operators can inspect replay payload before apply
3. replay imported activity rows into live confirm-activity trail with explicit status paths

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity replay controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay parser/import tokens:
  - `parseQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityText`
  - `parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityBundlePayload`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportSchemaHint`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportPreview`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityImportGuidance`
- replay action token:
  - `replayQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityTrailFromText`
- replay status strings:
  - `dry-run handoff apply confirm activity replay skipped: empty payload`
  - `dry-run handoff apply confirm activity replay failed:`
  - `dry-run handoff apply confirm activity replayed (`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_schema_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_preview`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_text`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_replay`

## Validation

Trust-audit apply dry-run handoff activity-replay token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. replay parser/import preview/guidance tokens exist
2. replay action/status + UI control tokens exist
3. API regression suite remains pass
