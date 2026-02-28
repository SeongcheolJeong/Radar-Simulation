#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportControlsTrailGuardControlsParserGuidance",
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportControlsTrailGuardParserGuidance",
    "guidance: parser waiting; controls-trail guard controls continuity active",
    "guidance: resolve parser errors; controls-trail guard controls continuity preserved",
    "guidance: controls-trail guard controls continuity active",
    "confirm activity replay trail import confirm trail import preview: waiting for JSON payload, controls_snapshot ",
    "controls_trail_guard ",
    "controls_trail_guard_controls ",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_controls_trail_guard_controls_parser_guidance",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, (
    "missing required strict-rollback trust-audit apply dry-run handoff activity-replay "
    "timeline-import-audit-controls-trail-guard-controls-parser-refresh tokens: "
    f"{missing}"
  )

  print("validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_controls_trail_guard_controls_parser_refresh: pass")


if __name__ == "__main__":
  run()
