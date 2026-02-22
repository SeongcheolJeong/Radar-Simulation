# Web E2E Graph Auto Contract Propagation (M17.7)

## Goal

Propagate frontend contract diagnostics into operator-visible run/gate outputs automatically so guard health is visible without manual refresh.

1. include contract warning counters in run summary text
2. include contract warning counters in policy gate result text
3. keep right-panel diagnostics in sync automatically after run/gate/validation changes

Implementation:

- run hook integration:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_graph_run_ops.mjs`
- gate hook integration:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`
- app/panel wiring:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- `useGraphRunOps` appends contract counters to run text surfaces:
  - `contract_warning_unique`
  - `contract_warning_attempts`
  - `contract_diagnostics:` block for summary rendering path
- `useGateOps` appends contract counters to `Policy Gate Result`.
- `app.mjs` auto-refreshes diagnostics snapshot when any of these texts change:
  - `graphRunText`
  - `gateResultText`
  - `validationText`
- `NodeInspectorPanel` shows `Contract Diagnostics (Auto)` using `contractDebugText`.

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
scripts/run_graph_lab_local.sh 8118 8138
curl -s "http://127.0.0.1:8138/health"
curl -s "http://127.0.0.1:8118/frontend/graph_lab/app.mjs" | rg -n "\\[graphRunText, gateResultText, validationText, refreshContractWarnings\\]|contractDebugText"
curl -s "http://127.0.0.1:8118/frontend/graph_lab/hooks/use_graph_run_ops.mjs" | rg -n "contract_warning_unique|contract_warning_attempts|contract_diagnostics:"
curl -s "http://127.0.0.1:8118/frontend/graph_lab/hooks/use_gate_ops.mjs" | rg -n "contract_warning_unique|contract_warning_attempts"
curl -s "http://127.0.0.1:8118/frontend/graph_lab/panels.mjs" | rg -n "Contract Diagnostics \\(Auto\\)"
```

Pass criteria:

1. run/gate text surfaces include automatic contract counters
2. app auto-refresh effect is wired to run/gate/validation text changes
3. right-panel auto diagnostics box token is present
