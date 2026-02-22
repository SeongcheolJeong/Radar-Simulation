# Web E2E Graph Row Detail Lazy-Expansion (M17.19)

## Goal

Expose rich row details without paying render cost for every row.

1. expand details only for rows the operator requests
2. support batch expand/collapse for the current visible window
3. keep detail output readable and scoped to each row

Implementation:

- row detail toggle and lazy formatter:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
- detail styling:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`

## Behavior Contract

- per-row controls:
  - `Details` / `Hide` toggle buttons in compact + full row actions
- batch controls:
  - `Expand Visible`
  - `Collapse Details`
- keyboard shortcuts:
  - `e`: expand visible rows
  - `x`: collapse all expanded row details
- lazy detail formatting:
  - detail content built on demand via `formatRowDetailText(row)` only when row is expanded
  - includes timestamp/source/run id, delta/snapshot/baseline, `note_json`
- UI classes:
  - `contract-row-detail-btn`
  - `contract-overlay-row-detail`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8150 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8130
curl -s "http://127.0.0.1:8130/frontend/graph_lab/panels.mjs" | rg -n "Expand Visible|Collapse Details|Details\\\"|buildContractRowKey|formatRowDetailText|toggleRowExpanded|contract-overlay-row-detail|contract-row-detail-btn|key === \\\"e\\\"|key === \\\"x\\\""
curl -s "http://127.0.0.1:8130/frontend/graph_lab_reactflow.html" | rg -n "contract-overlay-row-detail|contract-row-detail-btn"
```

Pass criteria:

1. per-row and batch detail control tokens are present
2. lazy detail rendering/helper tokens are present
3. backend regression remains pass
