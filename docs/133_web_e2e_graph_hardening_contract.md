# Web E2E Graph Hardening Contract (M16.5)

## Goal

Harden graph-run execution for repeated edit/run loops with three guarantees:

1. cache-aware rerun path for faster repeat executions
2. explicit cancel/retry controls for long or interrupted runs
3. failure payloads with concrete recovery guidance

Implementation:

- backend: `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/web_e2e_api.py`
- validator: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- frontend integration: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`

## API Additions

- `POST /api/graph/runs/{graph_run_id}/cancel`
  - cooperative cancel (`queued/running` -> cancel requested/canceled)
- `POST /api/graph/runs/{graph_run_id}/retry?async=0|1`
  - new graph run from source request + optional overrides

## Request Extensions (`POST /api/graph/runs`)

- `cache` object (optional):
  - `enable: bool` (default `true`)
  - `mode: auto|required|off` (default `auto`)
  - `reuse_graph_run_id: str` (optional explicit cache source)
- `rerun_from_node_id: str` (optional)
  - v1 partial rerun acceleration is supported for `RadarMap` node type
- `execution_options.debug_delay_s` (optional, validator/debug hook)

## Cache Behavior

- cache key includes graph payload, topological order, scene path+revision token, profile, and hybrid-estimation flag
- full-cache hit path:
  - copies `path_list.json`, `adc_cube.npz`, `radar_map.npz` from latest compatible completed run
- partial-cache hit path (`rerun_from_node_id` = RadarMap):
  - copies cached `path_list.json` + `adc_cube.npz`
  - recomputes `radar_map.npz` from cached ADC and current scene `map_config`

## Record/Summary Hardening

- graph run record enriched with:
  - `cache` metadata (`hit`, `hit_scope`, `source_graph_run_id`, request-mode details)
  - `control` metadata (`cancel_requested`, reason/time)
  - `failure` payload (`type`, `message`, traceback snippet) on failure
  - `recovery` payload (`recoverable`, hints, retry endpoint)
- graph summary execution block enriched with:
  - `execution.cache`
  - node-level `cache_hit` markers
  - `bridge_mode` values for full/partial cache or full recompute

## Startup Recovery

- stale active graph runs found at orchestrator boot (`queued/running/cancel_requested`) are marked failed-recoverable with retry guidance

## Frontend Wiring

- Graph Lab run result now surfaces:
  - cache hit/scope/source id
  - non-completed run recovery hints and retry endpoint
- Graph Lab controls added:
  - `Retry Last Run`
  - `Cancel Last Run`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Optional UI smoke:

```bash
scripts/run_graph_lab_local.sh 8110 8130
curl -s "http://127.0.0.1:8110/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8130" | \
  rg -n "Retry Last Run|Cancel Last Run|/api/graph/runs/.*/cancel|/api/graph/runs/.*/retry|cache_hit"
```

Pass criteria:

1. validator passes cache full-hit + partial-hit + cancel + retry + failure-recovery scenarios
2. graph run API remains backward-compatible for existing M16.0~M16.4 flows
3. Graph Lab exposes retry/cancel controls and shows cache/recovery signals in run panel
