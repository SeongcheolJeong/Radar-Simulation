# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Audit Parser Refresh (M17.96)

## Goal

Refresh import-confirm trail parser feedback to preserve controls snapshot continuity.

1. add parser guidance text that carries import-confirm controls snapshot context for empty/error/ready parser states
2. keep parser preview continuity by attaching controls snapshot context to preview output for all parser states
3. surface a dedicated controls-snapshot guidance line near parser schema/preview controls

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline-import audit parser refresh:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay timeline import-audit parser refresh tokens:
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportControlsSnapshotGuidance`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsHint`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportPreview`
- replay timeline import-audit parser refresh guidance/preview strings:
  - `guidance: parser waiting; controls snapshot continuity active`
  - `guidance: resolve parser errors; controls snapshot continuity preserved`
  - `guidance: controls snapshot continuity active`
  - `controls_snapshot `
- replay timeline import-audit parser refresh UI key:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_controls_snapshot_guidance`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import-audit-parser-refresh token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_parser_refresh.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. parser controls-snapshot guidance + preview continuity tokens exist
2. parser refresh guidance/preview strings and UI key exist
3. API regression suite remains pass
