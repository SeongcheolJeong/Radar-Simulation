#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "quickTelemetryStrictRollbackTrustAuditBundleApplySafety",
    "quickTelemetryStrictRollbackTrustAuditBundleApplySafetyHint",
    "quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked",
    "trust audit bundle apply blocked: replacement safety confirm required",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_safety_hint",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_confirm",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_confirm_checkbox",
    "confirm replace trust policy/override log from trust-audit handoff",
    "setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmChecked(false)",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required strict-rollback trust-audit apply safety-gate tokens: {missing}"

  print("validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_safety_gate: pass")


if __name__ == "__main__":
  run()
