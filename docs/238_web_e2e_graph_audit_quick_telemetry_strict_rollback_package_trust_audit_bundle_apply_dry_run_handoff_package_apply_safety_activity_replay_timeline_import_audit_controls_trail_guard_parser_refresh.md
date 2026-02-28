# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Audit Controls-Trail Guard Parser Refresh (M17.103)

## Goal

Refresh import-confirm controls-trail guard parser guidance so continuity-echo guard messaging keeps parity across import preview states (`empty/error/ready`).

1. add parser guidance branch dedicated to controls-trail guard continuity
2. append controls-trail guard context to import preview text in `empty/error/ready` states
3. keep existing parser guidance and controls snapshot continuity contracts backward-compatible while layering additive guard guidance

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline-import audit controls-trail guard parser refresh:
  - `/home/seongcheoljeong/workspace/Radar-Simulation/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay timeline import-audit controls-trail guard parser refresh tokens:
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportControlsTrailGuardParserGuidance`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportControlsSnapshotGuidance`
- replay timeline import-audit controls-trail guard parser guidance strings:
  - `guidance: parser waiting; controls-trail guard continuity active`
  - `guidance: resolve parser errors; controls-trail guard continuity preserved`
  - `guidance: controls-trail guard continuity active`
- replay timeline import-audit controls-trail guard parser preview strings:
  - `confirm activity replay trail import confirm trail import preview: waiting for JSON payload, controls_snapshot `
  - `controls_trail_guard `
- replay timeline import-audit controls-trail guard parser UI key:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_controls_trail_guard_parser_guidance`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import-audit-controls-trail-guard-parser-refresh token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/Radar-Simulation/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_controls_trail_guard_parser_refresh.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/Radar-Simulation/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. controls-trail guard parser guidance token and UI key exist
2. parser guidance/preview strings include controls-trail guard continuity across `empty/error/ready`
3. API regression suite remains pass
