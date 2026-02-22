# Web E2E Graph Filter Preset Transfer Import/Export (M17.28)

## Goal

Allow contract-overlay filter presets to be shared across operators/workstations.

1. export saved filter presets as a JSON bundle
2. copy/paste or load JSON for import
3. merge imported presets with runtime normalization + clear status feedback

Implementation:

- filter transfer bundle/parser + overlay controls:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- transfer helpers:
  - bundle builder: `buildFilterPresetExportBundle`
  - serializer: `serializeFilterPresetExportBundle`
  - parser: `parseFilterPresetImportText`
- transfer bundle shape:
  - `schema_version`
  - `kind: graph_lab_contract_overlay_filter_presets`
  - `exported_at_iso`
  - `presets`
- parser acceptance:
  - bundle form (`{..., presets: {...}}`)
  - direct preset-map form (`{preset_a: {...}, preset_b: {...}}`)
- normalization/safety:
  - names normalized with `normalizeFilterPresetName`
  - values normalized with `normalizeFilterPresetConfig`
  - empty/invalid payloads raise explicit import error status
- overlay transfer controls:
  - transfer group key: `co_filter_transfer_cfg`
  - actions:
    - `Export Filter Presets`
    - `Copy Filter Presets`
    - `Load Filter JSON`
    - `Import Filter Presets`
  - text/status keys:
    - `co_filter_transfer_text`
    - `co_filter_transfer_status`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8159 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8139
curl -s "http://127.0.0.1:8139/frontend/graph_lab/panels.mjs" | rg -n "buildFilterPresetExportBundle|serializeFilterPresetExportBundle|parseFilterPresetImportText|schema_version|graph_lab_contract_overlay_filter_presets|co_filter_transfer_cfg|Export Filter Presets|Copy Filter Presets|Load Filter JSON|Import Filter Presets|co_filter_transfer_text|co_filter_transfer_status"
```

Pass criteria:

1. transfer helper/parser tokens are present
2. transfer UI tokens are present
3. backend regression remains pass
