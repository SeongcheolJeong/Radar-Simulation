#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunSummary",
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHint",
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunPreview",
    "apply dry-run: policy",
    "override_diff added=",
    "apply dry-run preview: waiting for trust-audit handoff payload",
    "apply dry-run preview: blocked by parse error",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_hint",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_preview",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required strict-rollback trust-audit apply dry-run summary tokens: {missing}"

  print("validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_summary: pass")


if __name__ == "__main__":
  run()
