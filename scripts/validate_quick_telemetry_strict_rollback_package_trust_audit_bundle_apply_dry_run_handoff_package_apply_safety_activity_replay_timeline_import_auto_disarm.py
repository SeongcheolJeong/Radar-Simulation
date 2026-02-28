#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "QUICK_TELEMETRY_STRICT_ROLLBACK_TRUST_AUDIT_APPLY_DRY_RUN_HANDOFF_HYDRATE_CONFIRM_ACTIVITY_REPLAY_CONFIRM_TRAIL_IMPORT_CONFIRM_TIMEOUT_MS",
    "quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmArmedAtMs",
    "quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTickMs",
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmCountdownHint",
    "dry-run handoff apply confirm activity replay trail import confirm armed (within 20s or it auto-disarms)",
    "dry-run handoff apply confirm activity replay trail import confirm auto-disarmed: re-check confirm to import replay timeline",
    "dry-run handoff apply confirm activity replay trail import confirm disarmed",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_countdown_hint",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, (
    "missing required strict-rollback trust-audit apply dry-run handoff activity-replay timeline-import-auto-disarm tokens: "
    f"{missing}"
  )

  print("validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_auto_disarm: pass")


if __name__ == "__main__":
  run()
