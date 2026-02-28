# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Parser (M17.84)

## Goal

Add replay timeline import parser with schema guard + preview for dry-run handoff confirm-activity replay flow.

1. validate replay timeline import payload kind/schema/entries contract
2. surface replay timeline import guidance for common parse failures
3. show replay timeline import preview summary (kind/schema/event count/latest/exported timestamp)

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline import parser:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay timeline parser tokens:
  - `parseQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailText`
  - `parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPayload`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportSchemaHint`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportGuidance`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportPreview`
- replay timeline parser UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_schema_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_preview`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_guidance`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_text`
- replay timeline parser preview strings:
  - `confirm activity replay trail import preview: waiting for JSON payload`
  - `confirm activity replay trail import preview: invalid payload (`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import-parser token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_parser.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. replay timeline parser state/guidance/preview tokens exist
2. replay timeline parser UI keys and preview strings exist
3. API regression suite remains pass
