# Web E2E Graph Audit Quick Telemetry Import Filter-Bundle Strict/Compat Mode Toggle (M17.56)

## Goal

Add an explicit import-mode toggle so operators can choose strict contract parsing or compatibility parsing for filter-bundle handoff payloads.

1. `compat` mode accepts wrapped payload and legacy bare-object payload.
2. `strict` mode requires wrapped payload (`filter_bundle`) and required `kind/schema_version`.
3. mode is visible in UI, persisted in overlay prefs, and reflected in parse preview/status.

Implementation:

- mode option constants + parser guardrails + UI controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- mode constants and normalizer:
  - `QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_MODE_OPTIONS`
  - `normalizeQuickTelemetryDrilldownImportFilterBundleMode`
- parser contract:
  - `parseQuickTelemetryDrilldownImportFilterBundleText(rawText, opts = null)`
  - strict-mode errors:
    - `strict mode requires filter_bundle wrapper`
    - `strict mode requires kind=...`
    - `strict mode requires schema_version=...`
  - parsed payload includes `import_mode`
- persisted pref:
  - `quickTelemetryDrilldownImportFilterBundleMode`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_mode_label`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_mode_chip_<id>`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_mode_hint`

## Validation

Mode-toggle validation script:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_import_filter_bundle_mode.py
```

Pass criteria:

1. mode constants/normalizer/parser/UI tokens exist
2. strict-mode wrapper/kind/schema guards are present
3. parse result/status includes selected mode metadata
