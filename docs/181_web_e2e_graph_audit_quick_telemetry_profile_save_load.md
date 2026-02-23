# Web E2E Graph Audit Quick Telemetry Custom Profile Save/Load + Team Transfer (M17.48)

## Goal

Promote drilldown usage from ad-hoc toggles to reusable team-shared profiles.

1. persist custom quick telemetry drilldown profiles locally
2. load/save/delete profiles from UI with built-in/custom separation
3. enable team transfer via JSON export/copy/import

Implementation:

- profile model + UI + transfer:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- storage/default model:
  - `CONTRACT_OVERLAY_QUICK_TELEMETRY_DRILLDOWN_PROFILES_KEY`
  - `DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES`
  - `activeQuickTelemetryDrilldownProfile`
  - `quickTelemetryDrilldownProfileDraft`
- profile normalization/storage:
  - `normalizeQuickTelemetryDrilldownProfileName`
  - `normalizeQuickTelemetryDrilldownProfile`
  - `loadQuickTelemetryDrilldownProfiles`
  - `saveQuickTelemetryDrilldownProfiles`
- team transfer bundle:
  - `buildQuickTelemetryDrilldownProfileExportBundle`
  - `serializeQuickTelemetryDrilldownProfileExportBundle`
  - `parseQuickTelemetryDrilldownProfileImportText`
  - bundle kind: `graph_lab_contract_overlay_quick_telemetry_drilldown_profiles`
- operator actions:
  - `applyActiveQuickTelemetryDrilldownProfile`
  - `saveCurrentQuickTelemetryDrilldownProfile`
  - `deleteActiveQuickTelemetryDrilldownProfile`
  - `exportQuickTelemetryDrilldownProfilesToJson`
  - `copyQuickTelemetryDrilldownProfilesJson`
  - `importQuickTelemetryDrilldownProfilesFromText`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_cfg`
  - `co_filter_import_audit_quick_telemetry_profile_select`
  - `co_filter_import_audit_quick_telemetry_profile_save`
  - `co_filter_import_audit_quick_telemetry_profile_delete`
  - `co_filter_import_audit_quick_telemetry_profile_transfer_cfg`
  - `co_filter_import_audit_quick_telemetry_profile_export`
  - `co_filter_import_audit_quick_telemetry_profile_copy`
  - `co_filter_import_audit_quick_telemetry_profile_load_json`
  - `co_filter_import_audit_quick_telemetry_profile_import`
  - `co_filter_import_audit_quick_telemetry_profile_transfer_text`

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
curl -s "http://127.0.0.1:8171/frontend/graph_lab/panels.mjs" | rg -n "CONTRACT_OVERLAY_QUICK_TELEMETRY_DRILLDOWN_PROFILES_KEY|DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES|normalizeQuickTelemetryDrilldownProfileName|normalizeQuickTelemetryDrilldownProfile|loadQuickTelemetryDrilldownProfiles|saveQuickTelemetryDrilldownProfiles|buildQuickTelemetryDrilldownProfileExportBundle|serializeQuickTelemetryDrilldownProfileExportBundle|parseQuickTelemetryDrilldownProfileImportText|quickTelemetryDrilldownProfiles|activeQuickTelemetryDrilldownProfile|quickTelemetryDrilldownProfileDraft|quickTelemetryDrilldownTransferText|quickTelemetryDrilldownTransferStatus|quickTelemetryDrilldownProfileOptions|applyActiveQuickTelemetryDrilldownProfile|saveCurrentQuickTelemetryDrilldownProfile|deleteActiveQuickTelemetryDrilldownProfile|exportQuickTelemetryDrilldownProfilesToJson|copyQuickTelemetryDrilldownProfilesJson|importQuickTelemetryDrilldownProfilesFromText|co_filter_import_audit_quick_telemetry_profile_cfg|co_filter_import_audit_quick_telemetry_profile_select|co_filter_import_audit_quick_telemetry_profile_save|co_filter_import_audit_quick_telemetry_profile_delete|co_filter_import_audit_quick_telemetry_profile_transfer_cfg|co_filter_import_audit_quick_telemetry_profile_export|co_filter_import_audit_quick_telemetry_profile_copy|co_filter_import_audit_quick_telemetry_profile_load_json|co_filter_import_audit_quick_telemetry_profile_import|co_filter_import_audit_quick_telemetry_profile_transfer_text|graph_lab_contract_overlay_quick_telemetry_drilldown_profiles|drilldown profile transfer:"
```

Pass criteria:

1. backend regression remains pass
2. custom profile model/save-load tokens are present
3. team transfer(import/export/copy/load-json) tokens are present
