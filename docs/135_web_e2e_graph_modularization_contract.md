# Web E2E Graph Frontend Modularization Contract (M17.1)

## Goal

Reduce Graph Lab frontend coupling by moving inline script logic from HTML into reusable ES modules while preserving M16.5 + M17.0 behavior:

1. cache/cancel/retry execution controls remain intact
2. sync/async run mode and poll monitor remain intact
3. artifact inspector and gate workflows remain intact

Implementation:

- HTML shell: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
- entry/runtime modules:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/main.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/deps.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/constants.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/graph_helpers.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/run_monitor.mjs`

## Behavior Contract

- `graph_lab_reactflow.html` must only host style/layout shell + `#app` container + module entry load.
- Graph runtime logic must be loaded from `frontend/graph_lab/main.mjs` and `frontend/graph_lab/app.mjs`.
- Utility logic must be reusable modules:
  - graph schema/path helpers (`toFlowNode`, `toGraphPayload`, `normalizeRepoPath`)
  - async run monitor helpers (`clampPollIntervalMs`, `buildGraphRunRecordText`)
- Existing Graph API contracts and UI tokens from M16.5/M17.0 remain present in moduleized code:
  - `Run Graph (API)`, `Retry Last Run`, `Cancel Last Run`, `Poll Last Run`
  - `Run Mode`, `Auto Poll`, `poll_state`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
scripts/run_graph_lab_local.sh 8112 8132
curl -s "http://127.0.0.1:8112/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8132" | rg -n "graph_lab/main\.mjs"
curl -s "http://127.0.0.1:8112/frontend/graph_lab/app.mjs" | rg -n "Run Mode|Auto Poll|Poll Last Run|/api/graph/runs\?async=|/api/graph/runs/.*/retry\?async=|/api/graph/runs/.*/cancel"
```

Pass criteria:

1. HTML shell no longer contains inline app runtime block
2. module entry and app module are served by static server
3. M16.5/M17.0 control/endpoint tokens remain visible in app module
