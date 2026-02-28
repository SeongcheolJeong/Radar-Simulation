# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Safety Auto-Disarm (M17.70)

## Goal

Add timed auto-disarm for trust-audit apply replacement confirm with countdown hint.

1. arm apply-confirm with bounded safety window and auto-reset when timer expires
2. show countdown hint while armed so operators know remaining confirm window
3. clear armed timer state whenever risk/flow resets remove apply-confirm requirement

Implementation:

- strict-rollback trust-audit apply auto-disarm controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- apply-confirm timer tokens:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_CONFIRM_TIMEOUT_MS`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyConfirmCountdownHint`
- timer status strings:
  - `trust audit apply confirm armed: apply within 20s or it auto-disarms`
  - `trust audit apply confirm auto-disarmed: re-check confirm to apply`
- UI key:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_confirm_countdown_hint`

## Validation

Trust-audit apply auto-disarm token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_safety_auto_disarm.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. apply-confirm timer/counter state and hint tokens exist
2. auto-disarm status + countdown UI tokens exist
3. API regression suite remains pass
