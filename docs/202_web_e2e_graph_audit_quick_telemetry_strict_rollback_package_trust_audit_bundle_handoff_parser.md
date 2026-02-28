# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Handoff Parser (M17.67)

## Goal

Add trust-audit bundle handoff parser with strict schema guard and import preview.

1. parse trust-audit handoff JSON with kind/schema guard checks
2. validate required structures (`override_log`, `provenance_snapshot`) before preview
3. surface import schema hint, invalid-payload guidance, and preview summary in transfer panel

Implementation:

- strict-rollback trust-audit handoff parser controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- trust-audit parser tokens:
  - `parseQuickTelemetryStrictRollbackTrustAuditBundleText`
  - `parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload`
  - `quickTelemetryStrictRollbackTrustAuditBundleImportSchemaHint`
  - `quickTelemetryStrictRollbackTrustAuditBundleImportGuidance`
  - `quickTelemetryStrictRollbackTrustAuditBundleImportPreview`
- parser guard strings:
  - `trust audit bundle requires kind=`
  - `trust audit bundle requires schema_version=`
  - `unsupported schema_version (expected ... )`
  - `trust audit bundle missing override_log`
  - `trust audit bundle override_log.entries must be array`
  - `trust audit bundle missing provenance_snapshot`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_schema_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_preview`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_guidance`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_text`

## Validation

Trust-audit handoff parser token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_handoff_parser.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. trust-audit parser + schema-guard token set exists
2. trust-audit import preview/guidance UI tokens exist
3. API regression suite remains pass
