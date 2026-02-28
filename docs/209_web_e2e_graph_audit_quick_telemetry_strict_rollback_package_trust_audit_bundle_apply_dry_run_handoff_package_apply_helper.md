# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Helper (M17.74)

## Goal

Add dry-run handoff package apply helper that hydrates imported snapshot state and surfaces apply status.

1. add one-click apply action for parsed dry-run handoff package payloads
2. hydrate imported snapshot state for operator review (`hydrated_at` + summary/safety/bundle snapshot)
3. expose apply/reset status and hydrated preview near dry-run handoff import controls

Implementation:

- strict-rollback trust-audit apply dry-run handoff apply-helper controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- apply helper + hydrated snapshot tokens:
  - `applyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffFromText`
  - `resetQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot`
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedHint`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedPreview`
- apply status strings:
  - `dry-run handoff apply skipped: empty payload`
  - `dry-run handoff apply failed:`
  - `dry-run handoff snapshot hydrated (`
  - `dry-run handoff snapshot reset`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_reset`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_preview`

## Validation

Trust-audit apply dry-run handoff apply-helper token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_helper.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. apply-helper and hydrated-state tokens exist
2. apply/reset UI + status tokens exist
3. API regression suite remains pass
