#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "parseQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackageText",
    "parsedQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffPackagePayload",
    "quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffImportText",
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffImportSchemaHint",
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffImportGuidance",
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffImportPreview",
    "dry-run handoff package requires kind=",
    "dry-run handoff package requires schema_version=",
    "dry-run handoff package missing dry_run_summary",
    "dry-run handoff package missing apply_safety",
    "dry-run handoff package missing trust_audit_bundle_snapshot",
    "dry-run handoff import preview: waiting for JSON payload",
    "dry-run handoff import preview: invalid payload (",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_schema_hint",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_preview",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_guidance",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_text",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, (
    "missing required strict-rollback trust-audit apply dry-run handoff package parser tokens: "
    f"{missing}"
  )

  print("validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_parser: pass")


if __name__ == "__main__":
  run()
