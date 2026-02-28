# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Trust Audit Bundle Apply Dry-Run Handoff Package Apply Safety Activity Replay Gate (M17.80)

## Goal

Add replacement-risk safety gate for dry-run handoff confirm-activity replay.

1. detect replacement risk when replay payload differs from existing local confirm-activity trail
2. require explicit replace-confirm before replaying destructive activity overwrite
3. surface safety hint and confirm control near replay import actions for operator clarity

Implementation:

- strict-rollback trust-audit apply dry-run handoff safety activity replay gate controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replay-gate tokens:
  - `quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmChecked`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafety`
  - `quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplaySafetyHint`
- replay-gate status strings:
  - `dry-run handoff apply confirm activity replay blocked: replacement confirm required`
  - `dry-run handoff apply confirm activity replay confirm armed`
  - `dry-run handoff apply confirm activity replay confirm disarmed`
- replay-gate UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_safety_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_checkbox`

## Validation

Trust-audit apply dry-run handoff activity-replay gate token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_gate.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. replay replacement-risk safety state/hint tokens exist
2. replay blocked/arm/disarm status + confirm UI tokens exist
3. API regression suite remains pass
