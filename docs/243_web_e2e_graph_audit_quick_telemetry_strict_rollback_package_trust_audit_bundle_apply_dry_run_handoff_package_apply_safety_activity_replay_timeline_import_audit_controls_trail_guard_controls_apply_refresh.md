# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Audit Controls-Trail Guard Controls Apply Refresh (M17.108)

## Goal

Refresh import-confirm controls-trail guard controls apply continuity so continuity-echo guard-controls guidance stays in parity across apply continuity states.

1. extend apply continuity hint with controls-trail guard controls continuity context for `empty/error/confirm-required/apply-ready`
2. expose dedicated apply guard-controls continuity hint near existing apply continuity hints
3. keep existing apply continuity, controls snapshot continuity, and controls-trail guard continuity contracts stable while layering additive guard-controls guidance

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline-import audit controls-trail guard controls apply refresh:
  - `/home/seongcheoljeong/workspace/Radar-Simulation/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay timeline import-audit controls-trail guard controls apply refresh tokens:
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportApplyContinuityHint`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportApplyControlsTrailGuardContinuityHint`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportApplyControlsTrailGuardControlsContinuityHint`
- replay timeline import-audit controls-trail guard controls apply continuity strings:
  - `apply continuity: waiting for payload; controls snapshot unchanged`
  - `apply continuity: parser blocked; controls snapshot unchanged`
  - `apply continuity: replacement confirm required before alignment`
  - `apply continuity: apply will align controls snapshot after hydrate`
  - `controls-trail guard controls continuity active (`
  - `controls-trail guard controls continuity preserved (`
  - `controls-trail guard controls continuity pending (`
  - `controls-trail guard controls continuity aligned (`
- replay timeline import-audit controls-trail guard controls apply hint strings:
  - `apply guard-controls continuity: waiting for payload (`
  - `apply guard-controls continuity: parser blocked (`
  - `apply guard-controls continuity: replacement confirm required (`
  - `apply guard-controls continuity: apply-ready alignment (`
- replay timeline import-audit controls-trail guard controls apply UI key:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_apply_controls_trail_guard_controls_continuity_hint`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import-audit-controls-trail-guard-controls-apply-refresh token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/Radar-Simulation/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_controls_trail_guard_controls_apply_refresh.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/Radar-Simulation/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. apply continuity and dedicated apply guard-controls continuity hint tokens exist
2. apply continuity and apply guard-controls guidance include controls-trail guard controls parity across apply states
3. API regression suite remains pass
