# Web E2E Graph Filter Summary + Filter-Only Reset (M17.26)

## Goal

Make active filter scope immediately visible and reversible without disrupting current view state.

1. show active filter deltas as readable chips
2. provide one-click filter-only reset
3. keep compact/detail/shortcut settings untouched during filter reset

Implementation:

- filter summary token builder + reset action + overlay summary block:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- summary chips:
  - source/severity/policy/run/non-zero/gate-window/gate-pages/rows-window deltas
  - summary block keys:
    - `co_filter_summary`
    - `co_filter_summary_label`
    - `co_filter_summary_none`
    - `co_filter_token_<n>`
- reset behavior:
  - action: `Reset Filters` (`co_reset_filters`)
  - callback: `resetOverlayFilters`
  - resets only filter-scope controls to defaults:
    - source/severity/policy/run pin/non-zero
    - gate window/pages
    - rows/window + row offset
  - does not reset compact mode, detail fields, shortcut profiles/bindings
- quick-map completeness:
  - severity quick list includes `all`: `["all", "high", "med", "low"]`
  - policy quick list includes `all`: `["all", "hold", "adopt", "none"]`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8157 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8137
curl -s "http://127.0.0.1:8137/frontend/graph_lab/panels.mjs" | rg -n "resetOverlayFilters|activeFilterTokens|co_filter_summary|co_filter_summary_label|co_filter_summary_none|co_filter_token_|co_reset_filters|policy/severity/scoped/all|\\[\"all\", \"high\", \"med\", \"low\"\\]|\\[\"all\", \"hold\", \"adopt\", \"none\"\\]"
```

Pass criteria:

1. filter summary/reset tokens are present
2. quick-map completeness tokens are present
3. backend regression remains pass
