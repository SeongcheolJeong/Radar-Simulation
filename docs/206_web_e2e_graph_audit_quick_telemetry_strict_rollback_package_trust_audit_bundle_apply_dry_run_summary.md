# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Summary (M17.71)

## Goal

Add trust-audit apply dry-run diff summary that compares incoming handoff payload against live trust policy and override log state.

1. compute dry-run summary from incoming handoff policy/log vs live policy/log snapshot
2. expose one-line hint and multiline preview before apply action
3. keep dry-run summary parse-aware (`empty`, `error`, `ready`) to support safe operator flow

Implementation:

- strict-rollback trust-audit apply dry-run controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- dry-run summary tokens:
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunSummary`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHint`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunPreview`
- dry-run hint/preview strings:
  - `apply dry-run: policy ...`
  - `override_diff added=... removed=... changed=... unchanged=...`
  - `apply dry-run preview: waiting for trust-audit handoff payload`
  - `apply dry-run preview: blocked by parse error`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_preview`

## Validation

Trust-audit apply dry-run summary token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_summary.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. dry-run summary/hint/preview tokens exist
2. dry-run hint/preview UI tokens exist
3. API regression suite remains pass
