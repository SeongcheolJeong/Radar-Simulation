# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Audit Controls Import Confirm (M17.95)

## Goal

Harden import-confirm trail controls with explicit event-snapshot control status.

1. keep copy/export/reset controls for import-confirm trail while exposing snapshot-specific control status text
2. surface a dedicated controls hint so operators can see latest copy/export/reset control outcome inline
3. preserve existing global status strings so prior control contracts remain backward compatible

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline-import audit controls import-confirm status hint:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay timeline import-audit controls import-confirm tokens:
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsHint`
  - `copyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailJson`
  - `exportQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailToJson`
  - `resetQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrail`
- replay timeline import-audit controls import-confirm status strings:
  - `import confirm trail controls: event snapshot copied (`
  - `import confirm trail controls: event snapshot export complete (`
  - `import confirm trail controls: event snapshot reset`
- replay timeline import-audit controls import-confirm UI key:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_controls_hint`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import-audit-controls-import-confirm token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_controls_import_confirm.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. import-confirm trail controls status state/hint tokens exist
2. snapshot control status strings and controls hint UI key exist
3. API regression suite remains pass
