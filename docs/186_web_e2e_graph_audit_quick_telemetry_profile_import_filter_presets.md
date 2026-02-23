# Web E2E Graph Audit Quick Telemetry Profile Import Filter Presets + Reset Bundles (M17.53)

## Goal

Add operator-friendly quick presets and one-click reset bundles for drilldown profile import filter controls.

1. add filter preset chips with scoped counts (`all/changed/builtin/custom/new`)
2. add one-click filter bundle reset and safety bundle reset actions
3. surface active filter-bundle hint to reduce hidden-state confusion

Implementation:

- preset/bundle logic + UI:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- preset model:
  - `QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_PRESETS`
  - `resolveQuickTelemetryDrilldownImportFilterPreset`
  - `quickTelemetryDrilldownImportFilterPresetCounts`
  - `activeQuickTelemetryDrilldownImportFilterPresetId`
- bundle state/hints:
  - `quickTelemetryDrilldownImportFilterBundleHint`
  - `quickTelemetryDrilldownImportFilterBundleIsDefault`
  - `quickTelemetryDrilldownImportSafetyBundleIsDefault`
- preset/bundle actions:
  - `applyQuickTelemetryDrilldownImportFilterPreset`
  - `resetQuickTelemetryDrilldownImportFilterBundle`
  - `resetQuickTelemetryDrilldownImportSafetyBundle`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_presets`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_preset_chip_`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_reset`
  - `co_filter_import_audit_quick_telemetry_profile_import_safety_bundle_reset`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_hint`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend token contract smoke:

```bash
rg -n "QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_PRESETS|resolveQuickTelemetryDrilldownImportFilterPreset|quickTelemetryDrilldownImportFilterPresetCounts|activeQuickTelemetryDrilldownImportFilterPresetId|quickTelemetryDrilldownImportFilterBundleHint|quickTelemetryDrilldownImportFilterBundleIsDefault|quickTelemetryDrilldownImportSafetyBundleIsDefault|applyQuickTelemetryDrilldownImportFilterPreset|resetQuickTelemetryDrilldownImportFilterBundle|resetQuickTelemetryDrilldownImportSafetyBundle|co_filter_import_audit_quick_telemetry_profile_import_filter_presets|co_filter_import_audit_quick_telemetry_profile_import_filter_preset_chip_|co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_hint|co_filter_import_audit_quick_telemetry_profile_import_safety_bundle_reset" /Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs
```

Pass criteria:

1. backend regression remains pass
2. preset/bundle derivation + reset actions are present
3. preset chip/reset-bundle UI tokens are present
