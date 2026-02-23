# Web E2E Graph Audit Quick Telemetry Profile Import Guardrails + Rollback Hint (M17.49)

## Goal

Harden drilldown profile import with explicit overwrite visibility and safe rollback.

1. show import diff/merge preview before applying profile payload
2. block changed-overwrite import unless operator confirms
3. keep one-step rollback snapshot with undo hint/action

Implementation:

- guardrail logic + UI:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- import guardrail state:
  - `quickTelemetryDrilldownImportOverwriteConfirmChecked`
  - `quickTelemetryDrilldownImportUndoSnapshot`
- diff/preview derivation:
  - `parsedQuickTelemetryDrilldownProfileImportPayload`
  - `quickTelemetryDrilldownImportRows`
  - `quickTelemetryDrilldownImportHasChangedOverwrite`
  - `quickTelemetryDrilldownImportPreview`
  - `quickTelemetryDrilldownImportPreviewRows`
  - `quickTelemetryDrilldownImportRollbackHint`
  - `cloneNormalizedQuickTelemetryDrilldownProfiles`
- import/undo actions:
  - `importQuickTelemetryDrilldownProfilesFromText`
  - `undoLastQuickTelemetryDrilldownProfileImport`
  - overwrite protection status:
    - `import blocked: confirm overwrite changed profiles`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_confirm_label`
  - `co_filter_import_audit_quick_telemetry_profile_import_preview`
  - `co_filter_import_audit_quick_telemetry_profile_import_rollback_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_undo`
  - `co_filter_import_audit_quick_telemetry_profile_import_preview_row_`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8151 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8171
curl -s "http://127.0.0.1:8151/health"
curl -s "http://127.0.0.1:8171/frontend/graph_lab/panels.mjs" | rg -n "cloneNormalizedQuickTelemetryDrilldownProfiles|quickTelemetryDrilldownImportOverwriteConfirmChecked|quickTelemetryDrilldownImportUndoSnapshot|parsedQuickTelemetryDrilldownProfileImportPayload|quickTelemetryDrilldownImportRows|quickTelemetryDrilldownImportHasChangedOverwrite|quickTelemetryDrilldownImportPreview|quickTelemetryDrilldownImportRollbackHint|undoLastQuickTelemetryDrilldownProfileImport|import blocked: confirm overwrite changed profiles|rollback: undo available|co_filter_import_audit_quick_telemetry_profile_import_confirm_label|co_filter_import_audit_quick_telemetry_profile_import_preview|co_filter_import_audit_quick_telemetry_profile_import_rollback_hint|co_filter_import_audit_quick_telemetry_profile_import_undo|co_filter_import_audit_quick_telemetry_profile_import_preview_row_"
```

Pass criteria:

1. backend regression remains pass
2. import diff/merge preview + overwrite-confirm tokens are present
3. rollback hint/undo tokens are present
