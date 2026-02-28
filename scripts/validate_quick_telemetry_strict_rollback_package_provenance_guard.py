#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
  repo_root = Path(__file__).resolve().parents[1]
  panels_path = repo_root / "frontend/graph_lab/panels.mjs"
  text = panels_path.read_text(encoding="utf-8")

  required_tokens = [
    "QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SOURCE_STAMP",
    "QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_CHECKSUM_ALGO",
    "stableStringifyForChecksum",
    "computeFnv1a32Hex",
    "computeQuickTelemetryStrictRollbackDrillPackageChecksum",
    "normalizeQuickTelemetryStrictRollbackDrillPackageProvenance",
    "provenance_guard",
    "quickTelemetryStrictRollbackPackageProvenanceGuard",
    "quickTelemetryStrictRollbackPackageProvenanceHint",
    "rollback package replay blocked: checklist delta/provenance guard detected (confirm replay required)",
    "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_provenance_hint",
    "confirm replay when checklist delta/provenance guard exists",
  ]
  missing = [token for token in required_tokens if token not in text]
  assert not missing, f"missing required strict-rollback package provenance guard tokens: {missing}"

  print("validate_quick_telemetry_strict_rollback_package_provenance_guard: pass")


if __name__ == "__main__":
  run()
