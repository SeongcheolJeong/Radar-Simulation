# Web E2E Graph Run Bridge Contract (M16.2)

## Goal

Bridge validated graph contracts to executable backend runs so ReactFlow shell can submit graph runs and retrieve status/summary from API.

Implementation:

- API/backend: `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/web_e2e_api.py`
- validator harness: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- frontend hookup: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`

## Endpoints

- `POST /api/graph/runs`
  - supports `?async=0|1`
  - request body includes `graph` and `scene_json_path` (or SceneSource node params fallback)
- `GET /api/graph/runs`
- `GET /api/graph/runs/{graph_run_id}`
- `GET /api/graph/runs/{graph_run_id}/summary`

## Storage Layout

- `data/web_e2e/graph_runs/<graph_run_id>/graph_run_record.json`
- `data/web_e2e/graph_runs/<graph_run_id>/graph_run_summary.json`
- `data/web_e2e/graph_runs/<graph_run_id>/graph_payload.json`
- `data/web_e2e/graph_runs/<graph_run_id>/output/*` (path/adc/map artifacts)

## Execution Bridge Model (v1)

- graph contract is validated first (same schema as M16.0)
- runtime execution currently uses single-pass scene pipeline bridge:
  - `bridge_mode = scene_pipeline_single_pass_v1`
- per-node execution trace is still emitted to summary:
  - node id/type
  - status
  - output contract hint
  - selected artifact pointers

## Summary Contract

- `version = web_e2e_graph_run_summary_v1`
- includes:
  - graph metadata (`graph_id`, `node_count`, `edge_count`, `topological_order`)
  - execution node results (`execution.node_results`)
  - existing output summaries (`path_summary`, `adc_summary`, `radar_map_summary`, `quicklook`)
  - artifact pointers (`outputs.*`, `outputs.graph_run_summary_json`)

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
scripts/run_graph_lab_local.sh 8105 8125
curl -s "http://127.0.0.1:8105/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8125" | \
  rg -n "Run Graph \(API\)|/api/graph/runs|graph_run_summary_json|Graph Run Result"
```

Pass criteria:

1. graph run creation/list/get/summary endpoints all pass in API validator
2. sync graph run (`async=0`) returns completed record and readable summary
3. ReactFlow shell exposes run action and renders graph-run result block
