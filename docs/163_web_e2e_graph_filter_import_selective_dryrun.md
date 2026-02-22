# Web E2E Graph Selective Filter Preset Import + Dry-Run Rows (M17.30)

## Goal

Improve filter preset transfer workflow for mixed-team payloads.

1. allow choosing a subset of imported presets
2. expose per-preset dry-run conflict class before apply
3. prevent accidental no-op ambiguity with explicit status

Implementation:

- selective import model + UI + apply path:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- parsed payload model:
  - `parsedFilterImportPayload` (`imported/error/empty`)
  - `filterImportRows` (per-preset dry-run row model)
  - `selectedFilterImportNames` (current selected apply set)
- dry-run conflict classes:
  - `new`
  - `overwrite_custom`
  - `overwrite_builtin`
- selective controls:
  - bulk actions:
    - `co_filter_import_select_all`
    - `co_filter_import_select_none`
  - row list container: `co_filter_import_rows`
  - row selector key pattern: `co_filter_import_row_<name>`
- apply behavior:
  - import applies only selected preset names
  - empty selection -> `import skipped: no presets selected`
  - preview reflects selected subset (`selected 0 ... select presets to import`)

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8161 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8141
curl -s "http://127.0.0.1:8141/frontend/graph_lab/panels.mjs" | rg -n "parsedFilterImportPayload|filterImportRows|selectedFilterImportNames|co_filter_import_select_all|co_filter_import_select_none|co_filter_import_rows|co_filter_import_row_|selected 0|select presets to import|import skipped: no presets selected|replace_custom"
```

Pass criteria:

1. selective import model tokens are present
2. per-row selector and bulk selector UI tokens are present
3. backend regression remains pass
