# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle (M17.66)

## Goal

Add strict rollback trust-audit bundle export package that combines override log history with provenance snapshot state.

1. bundle override-log rows + trust-policy mode into a dedicated trust-audit package
2. attach provenance snapshot (`parse_state`, guard checks, package metadata) for replay-context handoff
3. expose trust-audit copy/export + preview/status UI for operators

Implementation:

- strict-rollback trust-audit bundle controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- trust-audit bundle constants/helpers:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION`
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND`
  - `normalizeQuickTelemetryStrictRollbackTrustAuditProvenanceSnapshot`
  - `buildQuickTelemetryStrictRollbackTrustAuditBundle`
  - `serializeQuickTelemetryStrictRollbackTrustAuditBundle`
- trust-audit bundle state/actions:
  - `quickTelemetryStrictRollbackTrustAuditProvenanceSnapshot`
  - `quickTelemetryStrictRollbackTrustAuditBundle`
  - `quickTelemetryStrictRollbackTrustAuditBundleHint`
  - `quickTelemetryStrictRollbackTrustAuditBundlePreview`
  - `copyQuickTelemetryStrictRollbackTrustAuditBundleJson`
  - `exportQuickTelemetryStrictRollbackTrustAuditBundleToJson`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_copy`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_export`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_preview`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_status`

## Validation

Trust-audit bundle token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. trust-audit bundle constants/helper/state/action tokens exist
2. trust-audit bundle copy/export/preview/status UI tokens exist
3. API regression suite remains pass
