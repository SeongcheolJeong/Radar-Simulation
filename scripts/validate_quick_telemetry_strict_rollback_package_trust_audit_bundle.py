#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_SCHEMA_VERSION",
    "QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_BUNDLE_KIND",
    "normalizeQuickTelemetryStrictRollbackTrustAuditProvenanceSnapshot",
    "buildQuickTelemetryStrictRollbackTrustAuditBundle",
    "serializeQuickTelemetryStrictRollbackTrustAuditBundle",
    "quickTelemetryStrictRollbackTrustAuditProvenanceSnapshot",
    "quickTelemetryStrictRollbackTrustAuditBundle",
    "quickTelemetryStrictRollbackTrustAuditBundleHint",
    "quickTelemetryStrictRollbackTrustAuditBundlePreview",
    "copyQuickTelemetryStrictRollbackTrustAuditBundleJson",
    "exportQuickTelemetryStrictRollbackTrustAuditBundleToJson",
    "quickTelemetryDrilldownStrictRollbackTrustAuditBundleStatus",
    "graph_lab_quick_telemetry_strict_rollback_trust_audit_bundle_",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_hint",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_copy",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_export",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_preview",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_status",
    "Copy Trust Audit Bundle",
    "Export Trust Audit Bundle",
    "trust audit bundle copied (",
    "trust audit bundle export complete (",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required strict-rollback package trust audit bundle tokens: {missing}"

  print("validate_quick_telemetry_strict_rollback_package_trust_audit_bundle: pass")


if __name__ == "__main__":
  run()
