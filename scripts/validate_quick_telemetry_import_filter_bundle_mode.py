#!/usr/bin/env python3
from pathlib import Path


def run() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    panels_path = repo_root / "frontend/graph_lab/panels.mjs"
    text = panels_path.read_text(encoding="utf-8")

    required_tokens = [
        "QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_MODE_OPTIONS",
        "normalizeQuickTelemetryDrilldownImportFilterBundleMode",
        "parseQuickTelemetryDrilldownImportFilterBundleText(rawText, opts = null)",
        "strict mode requires filter_bundle wrapper",
        "strict mode requires kind=",
        "strict mode requires schema_version=",
        "quickTelemetryDrilldownImportFilterBundleMode",
        "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_mode_label",
        "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_mode_chip_",
        "co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_mode_hint",
    ]

    missing = [token for token in required_tokens if token not in text]
    assert not missing, f"missing required mode-toggle tokens: {missing}"

    assert "mode: quickTelemetryDrilldownImportFilterBundleMode" in text
    assert "import_mode: mode" in text

    print("validate_quick_telemetry_import_filter_bundle_mode: pass")


if __name__ == "__main__":
    run()
