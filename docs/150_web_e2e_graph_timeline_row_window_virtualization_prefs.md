# Web E2E Graph Timeline Row-Window Virtualization + Pref Persistence (M17.17)

## Goal

Keep overlay usable under large timelines by reducing render volume and persisting operator knobs.

1. render only a window slice of filtered rows
2. allow explicit row-window navigation (`Top/Prev/Next`)
3. persist overlay settings across page reloads

Implementation:

- overlay windowing + persistence:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- render path:
  - uses `visibleRows` window instead of mapping full `filteredRows`
- row-window controls:
  - selector: `rows/window`
  - actions: `Top`, `Prev`, `Next`
  - status: `window start-end/filtered_count`
- overlay preference persistence:
  - storage key: `graph_lab_contract_overlay_prefs_v1`
  - load/save helpers:
    - `loadContractOverlayPrefs`
    - `saveContractOverlayPrefs`
  - persisted fields:
    - `sourceFilter`, `pinnedRunId`, `nonZeroOnly`, `compactMode`
    - `gateHistoryLimit`, `gateHistoryPages`
    - `rowWindowSize`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8148 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8128
curl -s "http://127.0.0.1:8128/frontend/graph_lab/panels.mjs" | rg -n "CONTRACT_OVERLAY_PREFS_KEY|loadContractOverlayPrefs|saveContractOverlayPrefs|rows/window|co_row_window_select|co_row_window_top|co_row_window_prev|co_row_window_next|visibleRows"
```

Pass criteria:

1. row-window virtualization tokens are present
2. preference persistence tokens are present
3. backend regression remains pass
