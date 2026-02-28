# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Policy (M17.65)

## Goal

Add strict trust policy for rollback package replay with explicit operator override logging.

1. trust policy modes (`strict_reject`, `compat_confirm`) for provenance guard handling
2. strict reject blocks replay on provenance issue until override replay is used
3. override replay events are logged/exportable with policy/provenance metadata

Implementation:

- strict-rollback package trust policy controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- trust policy tokens:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_POLICY_OPTIONS`
  - `normalizeQuickTelemetryStrictRollbackPackageTrustPolicy`
  - `quickTelemetryStrictRollbackPackageTrustPolicy`
  - `quickTelemetryStrictRollbackPackageTrustPolicyHint`
- operator override log tokens:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_LIMIT`
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_SCHEMA_VERSION`
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_KIND`
  - `normalizeQuickTelemetryStrictRollbackOverrideLogEntry`
  - `buildQuickTelemetryStrictRollbackOverrideLogBundle`
  - `serializeQuickTelemetryStrictRollbackOverrideLogBundle`
  - `quickTelemetryStrictRollbackPackageOverrideLogRows`
  - `quickTelemetryStrictRollbackPackageOverrideLogPreview`
  - `quickTelemetryStrictRollbackPackageOverrideLogHint`
  - `overrideReplayQuickTelemetryStrictRollbackPackageFromText`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_policy_label`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_policy_chip_`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_policy_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_replay`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_reason`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_copy`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_export`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_reset`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_preview`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_status`

## Validation

Trust-policy token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_policy.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. trust policy + override log tokens exist
2. trust-policy/override UI tokens exist
3. API regression suite remains pass
