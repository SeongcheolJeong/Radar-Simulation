#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "applyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffFromText",
    "resetQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot",
    "quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedSnapshot",
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedHint",
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydratedPreview",
    "dry-run handoff apply skipped: empty payload",
    "dry-run handoff apply failed:",
    "dry-run handoff snapshot hydrated (",
    "dry-run handoff snapshot reset",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_reset",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_hint",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_preview",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, (
    "missing required strict-rollback trust-audit apply dry-run handoff package apply-helper tokens: "
    f"{missing}"
  )

  print("validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_helper: pass")


if __name__ == "__main__":
  run()
