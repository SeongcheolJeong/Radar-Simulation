#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "QUICK_TELEMETRY_STRICT_ADOPTION_MIN_SUCCESS_COUNT",
    "quickTelemetryDrilldownStrictAdoptionSignals",
    "quickTelemetryDrilldownStrictAdoptionGateStatus",
    "bumpQuickTelemetryDrilldownStrictAdoptionSignals",
    "resetQuickTelemetryDrilldownStrictAdoptionSignals",
    "quickTelemetryDrilldownStrictAdoptionChecklist",
    "quickTelemetryDrilldownStrictAdoptionChecklistHint",
    "quickTelemetryDrilldownStrictAdoptionChecklistPreview",
    "strict default-switch checklist:",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_adoption_gate_hint",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_adoption_gate_preview",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_adoption_gate_reset",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_adoption_gate_status",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required strict-adoption gate tokens: {missing}"

  print("validate_quick_telemetry_strict_adoption_gate: pass")


if __name__ == "__main__":
  run()
