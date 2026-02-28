# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Auto-Disarm (M17.81)

## Goal

Add bounded auto-disarm safety for dry-run handoff confirm-activity replay replacement-confirm.

1. arm replay replacement-confirm with a strict timeout window (`20s`)
2. auto-disarm replay replacement-confirm when timeout expires
3. surface replay confirm countdown hint near replay controls for operator clarity

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity-replay auto-disarm controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay-auto-disarm tokens:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TIMEOUT_MS`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmArmedAtMs`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTickMs`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmCountdownHint`
- replay-auto-disarm status strings:
  - `dry-run handoff apply confirm activity replay confirm armed (within 20s or it auto-disarms)`
  - `dry-run handoff apply confirm activity replay confirm auto-disarmed: re-check confirm to replay`
  - `dry-run handoff apply confirm activity replay confirm disarmed`
- replay-auto-disarm UI key:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_countdown_hint`

## Validation

Trust-audit apply dry-run handoff activity-replay auto-disarm token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_auto_disarm.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. replay confirm timer/countdown token paths exist
2. replay arm/disarm/auto-disarm status + countdown UI token exists
3. API regression suite remains pass
