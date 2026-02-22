# Web E2E Graph Component + API Split Contract (M17.2)

## Goal

Refactor Graph Lab frontend into a clearer responsibility split while keeping M16.5/M17.0 run behavior unchanged:

1. `app.mjs` keeps state and orchestration only
2. panel rendering moves to component module(s)
3. network fetch logic moves to API client module

Implementation:

- orchestration: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
- API client: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/api_client.mjs`
- panel components: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- `app.mjs` no longer calls `fetch(...)` directly.
- Graph API routes are centralized in `api_client.mjs` wrappers.
- UI tokens and controls stay visible in componentized view:
  - `Run Mode`, `Auto Poll`, `Poll Last Run`
  - `Run Graph (API)`, `Retry Last Run`, `Cancel Last Run`
- Existing async run monitor and hardening semantics remain intact:
  - run/retry still bind `?async=...`
  - cancel endpoint binding remains present
  - summary fallback, recovery text, and gate report flow remain available

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
scripts/run_graph_lab_local.sh 8113 8133
curl -s "http://127.0.0.1:8113/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8133" | rg -n "graph_lab/main\.mjs"
curl -s "http://127.0.0.1:8113/frontend/graph_lab/app.mjs" | rg -n "GraphInputsPanel|GraphCanvasPanel|NodeInspectorPanel|runGraph\(|retryGraphRun\(|cancelGraphRun\("
curl -s "http://127.0.0.1:8113/frontend/graph_lab/api_client.mjs" | rg -n "/api/graph/runs\?async=|/retry\?async=|/cancel|/api/compare/policy|/api/baselines"
```

Pass criteria:

1. `app.mjs` has no direct `fetch(` usage
2. UI shell still renders moduleized controls/tokens
3. API endpoint strings are centralized in API client module
