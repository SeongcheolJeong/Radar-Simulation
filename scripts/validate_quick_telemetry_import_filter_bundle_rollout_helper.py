#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "buildQuickTelemetryDrilldownImportFilterBundleStrictWrapCandidate",
    "quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate",
    "quickTelemetryDrilldownImportFilterBundleStrictWrapHint",
    "quickTelemetryDrilldownImportFilterBundleStrictWrapPreview",
    "wrapQuickTelemetryDrilldownImportFilterBundleLegacyPayload",
    "legacy payload wrapped to strict bundle preview",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollout_hint",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_wrap_legacy",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_wrap_legacy_preview",
    "strict mode requires filter_bundle wrapper",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required rollout helper tokens: {missing}"

  print("validate_quick_telemetry_import_filter_bundle_rollout_helper: pass")


if __name__ == "__main__":
  run()
