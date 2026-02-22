# Web E2E Graph Input Model Grouping Contract (M17.4)

## Goal

Reduce action/state fan-out for `GraphInputsPanel` by grouping panel bindings into a single structured model while preserving existing operator behavior.

1. replace flat `state/actions` payload with grouped `model`
2. keep existing UI controls and run/gate semantics unchanged
3. improve maintainability for subsequent typed contracts

Implementation:

- app orchestration: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
- panel rendering: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- `GraphInputsPanel` consumes one `model` prop with grouped sections:
  - `values`
  - `setters`
  - `templateActions`
  - `graphActions`
  - `runActions`
  - `gateActions`
- `app.mjs` builds `inputPanelModel` and passes it as `model`.
- Existing controls remain unchanged:
  - `Run Mode`, `Auto Poll`, `Poll Last Run`
  - `Run Graph (API)`, `Retry Last Run`, `Cancel Last Run`
  - `Pin Baseline`, `Policy Gate`, `Export Gate Report (.md)`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
scripts/run_graph_lab_local.sh 8115 8135
curl -s "http://127.0.0.1:8115/frontend/graph_lab/app.mjs" | rg -n "inputPanelModel|model: inputPanelModel|values:|templateActions:|runActions:|gateActions:"
curl -s "http://127.0.0.1:8115/frontend/graph_lab/panels.mjs" | rg -n "GraphInputsPanel\(\{ model \}\)|const \{\s*values,|templateActions|runActions|gateActions|Run Mode|Auto Poll|Poll Last Run"
```

Pass criteria:

1. panel interface switched to grouped `model`
2. grouped sections contain all prior control bindings
3. backend regression and frontend token smoke both pass
