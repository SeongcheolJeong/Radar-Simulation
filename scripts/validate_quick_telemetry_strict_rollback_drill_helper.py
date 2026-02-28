#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PRESETS",
    "resolveQuickTelemetryStrictRollbackDrillPreset",
    "activeQuickTelemetryStrictRollbackDrillPresetId",
    "quickTelemetryDrilldownStrictRollbackChecklist",
    "quickTelemetryDrilldownStrictRollbackChecklistHint",
    "quickTelemetryDrilldownStrictRollbackChecklistPreview",
    "applyQuickTelemetryStrictRollbackDrillPreset",
    "resetQuickTelemetryStrictRollbackDrillPreset",
    "rollback drill preset applied (",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_checklist_hint",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_checklist_preview",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_preset_chip_",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_reset",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_status",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required strict-rollback drill helper tokens: {missing}"

  print("validate_quick_telemetry_strict_rollback_drill_helper: pass")


if __name__ == "__main__":
  run()
