#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "parseQuickTelemetryStrictRollbackTrustAuditBundleText",
    "trust audit bundle requires kind=",
    "trust audit bundle requires schema_version=",
    "unsupported schema_version (expected",
    "trust audit bundle missing override_log",
    "trust audit bundle override_log.entries must be array",
    "trust audit bundle missing provenance_snapshot",
    "parsedQuickTelemetryStrictRollbackTrustAuditBundlePayload",
    "quickTelemetryStrictRollbackTrustAuditBundleImportSchemaHint",
    "quickTelemetryStrictRollbackTrustAuditBundleImportPreview",
    "quickTelemetryStrictRollbackTrustAuditBundleImportGuidance",
    "trust audit import preview: waiting for JSON payload",
    "trust audit import preview: invalid payload",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_schema_hint",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_preview",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_guidance",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_text",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required strict-rollback trust-audit handoff parser tokens: {missing}"

  print("validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_handoff_parser: pass")


if __name__ == "__main__":
  run()
