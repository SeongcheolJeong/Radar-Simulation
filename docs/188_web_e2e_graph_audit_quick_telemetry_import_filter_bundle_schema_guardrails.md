# Web E2E Graph Audit Quick Telemetry Import Filter-Bundle Schema Guardrails (M17.55)

## Goal

Harden filter-bundle handoff with explicit kind/schema checks and actionable operator guidance on invalid payloads.

1. enforce bundle `kind/schema_version` guardrails when metadata is provided
2. show schema expectation hint near transfer controls
3. provide invalid-payload guidance for common parse failures (kind/schema/json/root)

Implementation:

- schema guardrail parser + hints:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- schema constants:
  - `QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_KIND`
  - `QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_SCHEMA_VERSION`
- parser guardrails:
  - `parseQuickTelemetryDrilldownImportFilterBundleText`
  - error paths:
    - `unexpected kind`
    - `unsupported schema_version`
- operator hint derivation:
  - `quickTelemetryDrilldownImportFilterBundleSchemaHint`
  - `quickTelemetryDrilldownImportFilterBundleInvalidGuidance`
  - `quickTelemetryDrilldownImportFilterBundlePreview` includes kind/schema/wrapper flags
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_schema_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_operator_hint`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend token contract smoke:

```bash
rg -n "QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_KIND|QUICK_TELEMETRY_DRILLDOWN_IMPORT_FILTER_BUNDLE_SCHEMA_VERSION|quickTelemetryDrilldownImportFilterBundleSchemaHint|quickTelemetryDrilldownImportFilterBundleInvalidGuidance|unsupported schema_version|unexpected kind|co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_schema_hint|co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_operator_hint" /Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs
```

Pass criteria:

1. backend regression remains pass
2. kind/schema guardrail tokens are present
3. schema hint + invalid guidance UI tokens are present
