#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "applyQuickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailFromText",
    "quickTelemetryStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailImportApplyContinuityHint",
    "quickTelemetryDrilldownStrictRollbackTrustAuditBundleApplyDryRunHandoffHydrateConfirmActivityReplayConfirmTrailImportConfirmTrailControlsStatus",
    "import confirm trail controls: apply skipped (empty payload)",
    "import confirm trail controls: apply blocked (parse error)",
    "import confirm trail controls: apply blocked (invalid payload)",
    "import confirm trail controls: apply blocked (replacement confirm required)",
    "import confirm trail controls: event snapshot aligned after apply (",
    "apply continuity: waiting for payload; controls snapshot unchanged",
    "apply continuity: parser blocked; controls snapshot unchanged",
    "apply continuity: replacement confirm required before alignment",
    "apply continuity: apply will align controls snapshot after hydrate",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_trust_audit_bundle_apply_dry_run_handoff_import_apply_confirm_activity_import_confirm_trail_import_confirm_trail_import_apply_continuity_hint",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, (
    "missing required strict-rollback trust-audit apply dry-run handoff activity-replay timeline-import-audit-apply-refresh tokens: "
    f"{missing}"
  )

  print("validate_quick_telemetry_strict_rollback_package_trust_audit_bundle_apply_dry_run_handoff_package_apply_safety_activity_replay_timeline_import_audit_apply_refresh: pass")


if __name__ == "__main__":
  run()
