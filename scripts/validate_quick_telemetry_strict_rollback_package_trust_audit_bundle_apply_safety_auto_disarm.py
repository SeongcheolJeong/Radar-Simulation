#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_CONFIRM_TIMEOUT_MS",
    "quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs",
    "quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs",
    "quickTelemetryStrictRollbackTrustAuditBundleApplyConfirmCountdownHint",
    "trust audit apply confirm auto-disarmed: re-check confirm to apply",
    "trust audit apply confirm armed: apply within 20s or it auto-disarms",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_confirm_countdown_hint",
    "apply confirm timer: check confirm to arm",
    "setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmArmedAtMs(0)",
    "setQuickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyConfirmTickMs(0)",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required strict-rollback trust-audit apply auto-disarm tokens: {missing}"

  print("validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_safety_auto_disarm: pass")


if __name__ == "__main__":
  run()
