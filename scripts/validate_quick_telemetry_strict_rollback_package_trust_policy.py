#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_POLICY_OPTIONS",
    "normalizeQuickTelemetryStrictRollbackPackageTrustPolicy",
    "quickTelemetryStrictRollbackPackageTrustPolicy",
    "quickTelemetryStrictRollbackPackageTrustPolicyHint",
    "QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_LIMIT",
    "QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_SCHEMA_VERSION",
    "QUICK_TELEMETRY_STRICT_ROLLBACK_OVERRIDE_LOG_KIND",
    "normalizeQuickTelemetryStrictRollbackOverrideLogEntry",
    "buildQuickTelemetryStrictRollbackOverrideLogBundle",
    "serializeQuickTelemetryStrictRollbackOverrideLogBundle",
    "quickTelemetryStrictRollbackPackageOverrideLogRows",
    "quickTelemetryStrictRollbackPackageOverrideLogPreview",
    "quickTelemetryStrictRollbackPackageOverrideLogHint",
    "overrideReplayQuickTelemetryStrictRollbackPackageFromText",
    "rollback package replay blocked: provenance strict-reject policy (use override replay)",
    "override log appended (",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_policy_label",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_policy_chip_",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_policy_hint",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_replay",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_reason",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_copy",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_export",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_reset",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_preview",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_override_log_status",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required strict-rollback package trust policy tokens: {missing}"

  print("validate_quick_telemetry_strict_rollback_package_trust_policy: pass")


if __name__ == "__main__":
  run()
