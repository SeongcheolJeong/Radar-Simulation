# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Safety Gate (M17.69)

## Goal

Add safety gate for trust-audit apply so replacement-risk updates require explicit operator confirmation.

1. compute apply safety risk from parsed handoff vs live trust policy/override log state
2. block apply when replacement risk exists until explicit confirm checkbox is armed
3. surface safety hint + replace-confirm control for operator clarity

Implementation:

- strict-rollback trust-audit apply safety-gate controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- apply safety-gate tokens:
  - `quickTelemetryStrictRollbackTrustAuditBundleApplySafety`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplySafetyHint`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked`
  - `trust audit bundle apply blocked: replacement safety confirm required`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_safety_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_confirm`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_confirm_checkbox`
  - `confirm replace trust policy/override log from trust-audit handoff`

## Validation

Trust-audit apply safety-gate token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_safety_gate.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. apply safety-gate state/hint/block tokens exist
2. safety hint + replace-confirm UI tokens exist
3. API regression suite remains pass
