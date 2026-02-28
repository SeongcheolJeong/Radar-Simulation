# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Parser (M17.73)

## Goal

Add strict parser + import preview for trust-audit apply dry-run handoff package payloads.

1. parse dry-run handoff package JSON with strict kind/schema guards
2. validate required sections (`dry_run_summary`, `apply_safety`, `trust_audit_bundle_snapshot`)
3. surface parse-aware import preview and guidance near dry-run handoff controls

Implementation:

- strict-rollback trust-audit apply dry-run handoff parser controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- parser + parse-state tokens:
  - `parseQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackageText`
  - `parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffImportText`
- schema guard/guidance/import-preview tokens:
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffImportSchemaHint`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffImportGuidance`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffImportPreview`
- parser error/preview strings:
  - `dry-run handoff package requires kind=`
  - `dry-run handoff package requires schema_version=`
  - `dry-run handoff package missing dry_run_summary`
  - `dry-run handoff package missing apply_safety`
  - `dry-run handoff package missing trust_audit_bundle_snapshot`
  - `dry-run handoff import preview: waiting for JSON payload`
  - `dry-run handoff import preview: invalid payload (`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_schema_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_preview`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_guidance`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_text`

## Validation

Trust-audit apply dry-run handoff package parser token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_parser.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. parser/schema-guard/import-preview tokens exist
2. handoff import UI tokens exist
3. API regression suite remains pass
