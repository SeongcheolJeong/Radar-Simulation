# Web E2E Graph Contract Diagnostics Surface (M17.6)

## Goal

Expose frontend contract-guard health in a developer-visible surface so invalid bindings can be detected and reset quickly.

1. track contract warning attempts/uniques by scope
2. expose snapshot/reset APIs from contract module
3. surface diagnostics in Graph Inputs panel with manual refresh/reset controls

Implementation:

- contract diagnostics API:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/contracts.mjs`
- UI wiring:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- contract module exports diagnostics APIs:
  - `getContractWarningSnapshot()`
  - `resetContractWarnings()`
- snapshot schema includes:
  - `contract_debug_version=contract_warning_debug_v1`
  - `unique_warning_count`
  - `attempt_count_total`
  - `by_scope[]`
  - `last_warning`
- Graph Inputs panel adds diagnostics controls:
  - `Contract Guard` section
  - `Refresh Guard` button
  - `Reset Guard` button
  - `contractDebugText` rendering box

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
scripts/run_graph_lab_local.sh 8117 8137
curl -s "http://127.0.0.1:8117/frontend/graph_lab/panels.mjs" | rg -n "Contract Guard|Refresh Guard|Reset Guard|contractDebugText"
curl -s "http://127.0.0.1:8117/frontend/graph_lab/contracts.mjs" | rg -n "getContractWarningSnapshot|resetContractWarnings|contract_warning_debug_v1"
curl -s "http://127.0.0.1:8117/frontend/graph_lab/app.mjs" | rg -n "refreshContractWarnings|resetContractWarnings|getContractWarningSnapshot|contractDebugText"
```

Pass criteria:

1. diagnostics API tokens and debug version are served from contract module
2. Graph Inputs panel shows diagnostics controls/tokens
3. app wiring binds refresh/reset actions and debug text state
