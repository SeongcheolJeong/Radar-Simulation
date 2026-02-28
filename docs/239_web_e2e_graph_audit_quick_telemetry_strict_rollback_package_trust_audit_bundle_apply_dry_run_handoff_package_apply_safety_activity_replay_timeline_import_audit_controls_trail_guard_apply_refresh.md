# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Timeline Import Audit Controls-Trail Guard Apply Refresh (M17.104)

## Goal

Refresh import-confirm controls-trail guard apply continuity so continuity-echo guard guidance remains in parity across apply continuity states.

1. extend apply continuity hint with controls-trail guard continuity context for `empty/error/confirm-required/apply-ready`
2. expose dedicated apply guard continuity hint near the apply continuity hint
3. keep existing apply continuity and controls snapshot contracts backward-compatible while adding additive guard guidance text

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay timeline-import audit controls-trail guard apply refresh:
  - `/home/seongcheoljeong/workspace/Radar-Simulation/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay timeline import-audit controls-trail guard apply refresh tokens:
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportApplyContinuityHint`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportApplyControlsTrailGuardContinuityHint`
- replay timeline import-audit controls-trail guard apply continuity strings:
  - `apply continuity: waiting for payload; controls snapshot unchanged`
  - `apply continuity: parser blocked; controls snapshot unchanged`
  - `apply continuity: replacement confirm required before alignment`
  - `apply continuity: apply will align controls snapshot after hydrate`
  - `controls-trail guard continuity active (`
  - `controls-trail guard continuity preserved (`
  - `controls-trail guard continuity pending (`
  - `controls-trail guard continuity aligned (`
- replay timeline import-audit controls-trail guard apply hint strings:
  - `apply guard continuity: waiting for payload (`
  - `apply guard continuity: parser blocked (`
  - `apply guard continuity: replacement confirm required (`
  - `apply guard continuity: apply-ready alignment (`
- replay timeline import-audit controls-trail guard apply UI key:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_apply_controls_trail_guard_continuity_hint`

## Validation

Trust-audit apply dry-run handoff activity-replay timeline-import-audit-controls-trail-guard-apply-refresh token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/Radar-Simulation/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_controls_trail_guard_apply_refresh.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/Radar-Simulation/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. apply continuity and dedicated apply guard continuity hint tokens exist
2. apply continuity and apply guard guidance strings include controls-trail guard parity across apply states
3. API regression suite remains pass
