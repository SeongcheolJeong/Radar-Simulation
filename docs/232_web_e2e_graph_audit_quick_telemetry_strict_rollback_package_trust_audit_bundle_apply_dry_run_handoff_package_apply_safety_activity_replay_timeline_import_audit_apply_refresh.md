# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Audit Apply Refresh (M17.97)

## Goal

Refresh import-confirm trail apply flow so control snapshot status stays aligned with apply outcomes.

1. align controls status updates with apply outcomes (empty, parse error, invalid payload, confirm block, hydrate success)
2. add post-apply continuity hint that explains control snapshot continuity near the apply action
3. keep existing global apply status strings intact while adding scoped control-snapshot alignment status

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline-import audit apply refresh:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay timeline import-audit apply refresh tokens:
  - `applyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailFromText`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportApplyContinuityHint`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus`
- replay timeline import-audit apply refresh status strings:
  - `import confirm trail controls: apply skipped (empty payload)`
  - `import confirm trail controls: apply blocked (parse error)`
  - `import confirm trail controls: apply blocked (invalid payload)`
  - `import confirm trail controls: apply blocked (replacement confirm required)`
  - `import confirm trail controls: event snapshot aligned after apply (`
- replay timeline import-audit apply refresh continuity hints:
  - `apply continuity: waiting for payload; controls snapshot unchanged`
  - `apply continuity: parser blocked; controls snapshot unchanged`
  - `apply continuity: replacement confirm required before alignment`
  - `apply continuity: apply will align controls snapshot after hydrate`
- replay timeline import-audit apply refresh UI key:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_apply_continuity_hint`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import-audit-apply-refresh token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_apply_refresh.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. apply refresh control-status + continuity-hint tokens exist
2. apply alignment status strings and continuity hint UI key exist
3. API regression suite remains pass
