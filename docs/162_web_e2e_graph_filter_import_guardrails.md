# Web E2E Graph Filter Preset Import Guardrails (M17.29)

## Goal

Make filter preset import safer for team sharing workflows.

1. let operator choose import strategy (`merge` vs `replace custom`)
2. show import conflict preview before apply
3. block invalid payload import from accidental apply

Implementation:

- import-mode + preview guardrail wiring:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- import mode model:
  - options: `merge`, `replace_custom`
  - option labels:
    - `merge (overwrite same name)`
    - `replace custom presets`
  - normalizer: `normalizeFilterImportMode`
  - persisted in overlay prefs as `filterImportMode`
- preview model:
  - computed string: `preview: total/new/overwrite/built-in overwrite/mode`
  - parse errors surface `preview: invalid payload (...)`
  - preview UI key: `co_filter_import_preview`
- apply guardrails:
  - import button key: `co_filter_import_presets`
  - import disabled when:
    - transfer text is empty
    - preview reports invalid payload
  - `replace_custom` behavior:
    - preserves built-in presets
    - replaces existing custom presets with imported set

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8160 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8140
curl -s "http://127.0.0.1:8140/frontend/graph_lab/panels.mjs" | rg -n "FILTER_IMPORT_MODE_OPTIONS|normalizeFilterImportMode|filterImportMode|filterImportPreview|co_filter_import_mode_select|co_filter_import_preview|replace_custom|graph_lab_contract_overlay_filter_presets"
```

Pass criteria:

1. mode/preview guardrail tokens are present
2. invalid payload import disable guard is present
3. backend regression remains pass
