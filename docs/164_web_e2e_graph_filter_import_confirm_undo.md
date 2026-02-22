# Web E2E Graph Replace Import Confirmation + Undo (M17.31)

## Goal

Prevent accidental destructive import in `replace_custom` mode and provide immediate rollback.

1. require explicit confirmation before replace-mode apply
2. capture pre-import snapshot for rollback
3. support one-click undo with status feedback

Implementation:

- replace-confirm + undo workflow:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- replace confirmation:
  - state: `filterReplaceConfirmChecked`
  - control key: `co_filter_replace_confirm`
  - mode-gated requirement:
    - apply blocked when `replace_custom` and confirmation unchecked
    - status: `confirm required: enable replace confirmation for replace custom`
  - safety reset:
    - confirmation resets when import payload text changes
- undo snapshot + restore:
  - snapshot state: `filterImportUndoSnapshot`
  - snapshot helper: `cloneNormalizedFilterPresets`
  - undo action key: `co_filter_import_undo`
  - undo hint key: `co_filter_import_undo_hint`
  - restore scope:
    - filter preset map
    - active preset
    - preset draft name
  - restore status: `undo restored snapshot (...)`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8162 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8142
curl -s "http://127.0.0.1:8142/frontend/graph_lab/panels.mjs" | rg -n "cloneNormalizedFilterPresets|filterReplaceConfirmChecked|filterImportUndoSnapshot|undoLastFilterImport|replaceImportNeedsConfirmation|co_filter_replace_confirm|co_filter_import_undo|co_filter_import_undo_hint|confirm required: enable replace confirmation for replace custom|undo restored snapshot|co_filter_import_presets"
```

Pass criteria:

1. replace confirmation + undo model tokens are present
2. UI/status tokens for confirm and undo are present
3. backend regression remains pass
