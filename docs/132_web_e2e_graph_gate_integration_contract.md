# Web E2E Graph Gate Integration Contract (M16.4)

## Goal

Enable a graph-run centered gate loop in ReactFlow shell:

1. pin baseline from graph-run summary
2. evaluate policy gate for latest graph run
3. export markdown gate report for handoff

Implementation:

- frontend: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
- backend robustness update: `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/web_e2e_api.py`
- validation harness: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`

## UI Controls

- `Baseline ID` input
- `Pin Baseline` button
- `Policy Gate` button
- `Export Gate Report (.md)` button
- `Policy Gate Result` panel

## API Wiring

- baseline pin:
  - `POST /api/baselines`
  - payload uses `summary_json=<graph_run_summary_json>`, `overwrite=true`
- policy gate:
  - `POST /api/compare/policy`
  - payload uses `baseline_id` + `candidate_summary_json=<graph_run_summary_json>`
- report export:
  - frontend markdown generation from latest `policy_eval` + graph summary pointers

## Backend Compatibility Fix

Graph summary-based baseline payloads may carry `run_id=None`.  
Resolver now treats `"None"`/`"null"` tokens as empty so summary-json path takes precedence.

Updated function:

- `_resolve_target_with_optional_prefix` in `web_e2e_api.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
scripts/run_graph_lab_local.sh 8108 8128
curl -s "http://127.0.0.1:8108/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8128" | \
  rg -n "Pin Baseline|Policy Gate|Export Gate Report|Policy Gate Result|/api/compare/policy|/api/baselines"
```

Pass criteria:

1. API validator passes graph-summary baseline + policy gate scenario
2. Graph Lab exposes baseline pin/gate/report controls
3. gate result panel and endpoint wiring tokens are present
