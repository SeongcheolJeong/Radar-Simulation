#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_LIMIT",
    "QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_SCHEMA_VERSION",
    "QUICK_TELEMETRY_STRICT_CUTOVER_LEDGER_KIND",
    "buildQuickTelemetryDrilldownStrictAdoptionChecklist",
    "normalizeQuickTelemetryDrilldownStrictCutoverLedgerEntry",
    "buildQuickTelemetryDrilldownStrictCutoverLedgerBundle",
    "serializeQuickTelemetryDrilldownStrictCutoverLedgerBundle",
    "appendQuickTelemetryDrilldownStrictCutoverLedgerEvent",
    "quickTelemetryDrilldownStrictCutoverLedger",
    "quickTelemetryDrilldownStrictCutoverTimelineHint",
    "quickTelemetryDrilldownStrictCutoverTimelinePreview",
    "exportQuickTelemetryDrilldownStrictCutoverLedgerToJson",
    "copyQuickTelemetryDrilldownStrictCutoverLedgerJson",
    "resetQuickTelemetryDrilldownStrictCutoverLedger",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_hint",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_export",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_copy",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_reset",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_preview",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_cutover_timeline_status",
    "cutover timeline event logged:",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required strict-cutover timeline tokens: {missing}"

  print("validate_quick_telemetry_strict_cutover_timeline: pass")


if __name__ == "__main__":
  run()
