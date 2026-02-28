#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "applyQuickTelemetryStrictRollbackTrustAuditBundleFromText",
    "trust audit bundle apply skipped: empty payload",
    "trust audit bundle apply failed:",
    "trust audit bundle apply failed: invalid payload",
    "override log hydrated from trust audit bundle (",
    "trust audit bundle applied (policy=",
    "setQuickTelemetryStrictRollbackPackageTrustPolicy(policyMode)",
    "setQuickTelemetryDrilldownStrictRollbackPackageOverrideLog(overrideEntries)",
    "setQuickTelemetryDrilldownStrictRollbackPackageOverrideReasonText(\"\")",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_import_apply",
    "Apply Trust Audit Bundle",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required strict-rollback trust-audit apply-helper tokens: {missing}"

  print("validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_helper: pass")


if __name__ == "__main__":
  run()
