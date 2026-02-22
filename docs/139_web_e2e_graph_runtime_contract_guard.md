# Web E2E Graph Runtime Contract Guard (M17.5)

## Goal

Introduce typed interface contracts and runtime guards for Graph Lab panel/hook bindings so frontend modules degrade safely when wiring is incomplete or malformed.

1. define typed contracts for panel model and hook option shapes
2. normalize/guard bindings at runtime
3. preserve existing run/gate operator behavior

Implementation:

- contract module: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/contracts.mjs`
- integration points:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_graph_run_ops.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`

## Behavior Contract

- `contracts.mjs` exports normalized contract builders:
  - `normalizeGraphInputsPanelModel` (`graph_inputs_panel_model_v1`)
  - `normalizeGraphRunOpsOptions` (`graph_run_ops_options_v1`)
  - `normalizeGateOpsOptions` (`gate_ops_options_v1`)
- runtime guard policy:
  - type mismatch/missing binding -> one-time warning (`console.warn`) with contract scope tag
  - missing function bindings -> stable no-op fallback
  - missing scalar/array bindings -> deterministic default value
- integration behavior:
  - `app.mjs` builds guarded input panel model before passing to panel
  - `GraphInputsPanel` normalizes incoming model defensively
  - run/gate hooks normalize option objects before action callbacks are built

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
scripts/run_graph_lab_local.sh 8116 8136
curl -s "http://127.0.0.1:8116/frontend/graph_lab/contracts.mjs" | rg -n "graph_inputs_panel_model_v1|graph_run_ops_options_v1|gate_ops_options_v1|normalizeGraphInputsPanelModel|normalizeGraphRunOpsOptions|normalizeGateOpsOptions"
curl -s "http://127.0.0.1:8116/frontend/graph_lab/app.mjs" | rg -n "normalizeGraphInputsPanelModel\(|inputPanelModel"
curl -s "http://127.0.0.1:8116/frontend/graph_lab/panels.mjs" | rg -n "normalizeGraphInputsPanelModel\(|GraphInputsPanel\(\{ model \}\)"
curl -s "http://127.0.0.1:8116/frontend/graph_lab/hooks/use_graph_run_ops.mjs" | rg -n "normalizeGraphRunOpsOptions\(" 
curl -s "http://127.0.0.1:8116/frontend/graph_lab/hooks/use_gate_ops.mjs" | rg -n "normalizeGateOpsOptions\(" 
```

Pass criteria:

1. contract module and version tokens are served
2. app/panel/hook integration points reference guard normalizers
3. backend regression and frontend token smoke both pass
