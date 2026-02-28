# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Audit Controls Refresh (M17.100)

## Goal

Refresh import-confirm controls lifecycle so continuity-echo status stays aligned across copy/export/reset actions.

1. align copy/export/reset controls-status messages with explicit continuity-echo marker
2. expose dedicated continuity lifecycle hint near import-confirm controls
3. keep existing controls contract and statuses backward-compatible while adding additive continuity alignment text

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline-import audit controls refresh:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay timeline import-audit controls refresh tokens:
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsContinuityHint`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus`
  - `copyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailJson`
  - `exportQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailToJson`
  - `resetQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail`
- replay timeline import-audit controls refresh status strings:
  - `continuity echo aligned`
  - `import confirm trail controls: event snapshot copied (`
  - `import confirm trail controls: event snapshot export complete (`
  - `import confirm trail controls: event snapshot reset`
- replay timeline import-audit controls refresh UI key:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_controls_continuity_hint`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import-audit-controls-refresh token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_controls_refresh.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. controls continuity-hint/state and copy/export/reset callback tokens exist
2. continuity-echo status markers and controls continuity UI key exist
3. API regression suite remains pass
