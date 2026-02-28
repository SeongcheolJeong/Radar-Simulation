#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_SCHEMA_VERSION",
    "QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_KIND",
    "buildQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackage",
    "serializeQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackage",
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload",
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackageHint",
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePreview",
    "copyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackageJson",
    "exportQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackageToJson",
    "quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffStatus",
    "dry-run handoff package copied (",
    "dry-run handoff package export complete (",
    "graph_lab_quick_telemetry_strict_rollback_trust_audit_apply_dry_run_handoff_package_",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_hint",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_copy",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_export",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_preview",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_status",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required strict-rollback trust-audit apply dry-run handoff package tokens: {missing}"

  print("validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package: pass")


if __name__ == "__main__":
  run()
