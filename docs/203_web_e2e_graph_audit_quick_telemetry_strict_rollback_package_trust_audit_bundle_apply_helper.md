# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Helper (M17.68)

## Goal

Add trust-audit handoff apply helper that hydrates rollback trust policy and override log from parsed bundle payload.

1. apply parsed trust-audit bundle directly to rollback trust-policy control
2. hydrate override log rows from handoff `override_log.entries`
3. expose explicit apply action/status in transfer panel with invalid/empty guard handling

Implementation:

- strict-rollback trust-audit apply helper controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- apply helper tokens:
  - `applyQuickTelemetryStrictRollbackTrustAuditBundleFromText`
  - `trust audit bundle apply skipped: empty payload`
  - `trust audit bundle apply failed: ...`
  - `trust audit bundle apply failed: invalid payload`
  - `override log hydrated from trust audit bundle (...)`
  - `trust audit bundle applied (policy=...)`
- apply hydrate state updates:
  - `setQuickTelemetryStrictRollbackPackageTrustPolicy(policyMode)`
  - `setQuickTelemetryDrilldownStrictRollbackPackageOverrideLog(overrideEntries)`
  - `setQuickTelemetryDrilldownStrictRollbackPackageOverrideReasonText("")`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_apply`
  - `Apply Trust Audit Bundle`

## Validation

Trust-audit apply-helper token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_helper.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. trust-audit apply helper + hydrate state tokens exist
2. trust-audit apply action UI token exists
3. API regression suite remains pass
