#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "quickTelemetryDrilldownStrictCutoverStatus",
    "quickTelemetryDrilldownStrictCutoverHint",
    "quickTelemetryDrilldownCompatFallbackReminder",
    "applyQuickTelemetryStrictDefaultCutoverPreset",
    "switchQuickTelemetryToCompatFallback",
    "strict default cutover preset applied (mode=strict)",
    "compat fallback preset applied (legacy payload support restored)",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_hint",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_apply",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_compat",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_reminder",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_status",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required strict-cutover helper tokens: {missing}"

  print("validate_quick_telemetry_strict_cutover_helper: pass")


if __name__ == "__main__":
  run()
