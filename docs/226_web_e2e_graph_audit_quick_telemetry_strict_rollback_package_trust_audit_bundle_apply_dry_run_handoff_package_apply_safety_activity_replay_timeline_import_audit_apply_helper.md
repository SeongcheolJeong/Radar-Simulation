# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Audit Apply Helper (M17.91)

## Goal

Add replay timeline-import confirm-trail apply helper for dry-run handoff confirm-activity replay flow.

1. provide one-click apply action to hydrate import-confirm trail from parsed audit import payload
2. keep explicit status paths for empty payload, parse error, invalid payload, and successful hydrate
3. surface apply action near import-confirm trail parser controls for operator continuity

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline-import audit apply helper:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay-timeline-import-audit-apply-helper tokens:
  - `applyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailFromText`
  - `parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPayload`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail`
- replay-timeline-import-audit-apply-helper UI key:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_apply`
- replay-timeline-import-audit-apply-helper status strings:
  - `dry-run handoff apply confirm activity replay trail import confirm trail import skipped: empty payload`
  - `dry-run handoff apply confirm activity replay trail import confirm trail import failed: `
  - `dry-run handoff apply confirm activity replay trail import confirm trail import failed: invalid payload`
  - `dry-run handoff apply confirm activity replay trail import confirm trail hydrated (`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import-audit-apply-helper token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_apply_helper.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. timeline-import confirm-trail apply-helper callback/state tokens exist
2. timeline-import confirm-trail apply button key + status strings exist
3. API regression suite remains pass
