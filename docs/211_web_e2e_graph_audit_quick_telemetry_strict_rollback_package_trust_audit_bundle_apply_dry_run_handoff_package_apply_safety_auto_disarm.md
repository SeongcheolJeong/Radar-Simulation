# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Auto-Disarm (M17.76)

## Goal

Add timed auto-disarm for dry-run handoff hydrate replace-confirm with countdown hint.

1. arm hydrate-confirm with bounded safety window and auto-reset when timer expires
2. show countdown hint while armed so operators can see remaining confirm window
3. clear armed timer state whenever hydrate risk/flow resets remove confirm requirement

Implementation:

- strict-rollback trust-audit apply dry-run handoff auto-disarm controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- hydrate-confirm timer tokens:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_TIMEOUT_MS`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmArmedAtMs`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmTickMs`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmCountdownHint`
- timer status strings:
  - `dry-run handoff apply confirm armed: hydrate overwrite is enabled (within 20s or it auto-disarms)`
  - `dry-run handoff apply confirm auto-disarmed: re-check confirm to hydrate`
- UI key:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_countdown_hint`

## Validation

Trust-audit apply dry-run handoff auto-disarm token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_auto_disarm.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. hydrate-confirm timer/counter state and hint tokens exist
2. auto-disarm status + countdown UI token exists
3. API regression suite remains pass
