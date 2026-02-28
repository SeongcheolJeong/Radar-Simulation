#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "parseQuickTelemetryStrictRollbackDrillPackageText",
    "parsedQuickTelemetryStrictRollbackDrillPackagePayload",
    "quickTelemetryStrictRollbackPackageChecklistDeltaGuard",
    "quickTelemetryStrictRollbackPackageChecklistDeltaHint",
    "quickTelemetryStrictRollbackPackageReplayPreview",
    "quickTelemetryDrilldownStrictRollbackPackageReplayText",
    "quickTelemetryDrilldownStrictRollbackPackageDeltaConfirmChecked",
    "replayQuickTelemetryStrictRollbackPackageFromText",
    "rollback package replay blocked: checklist delta detected (confirm replay required)",
    "rollback package replayed (",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_replay_preview",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_delta_hint",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_delta_confirm",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_delta_confirm_checkbox",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_replay",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_replay_text",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required strict-rollback package replay helper tokens: {missing}"

  print("validate_quick_telemetry_strict_rollback_package_replay_helper: pass")


if __name__ == "__main__":
  run()
