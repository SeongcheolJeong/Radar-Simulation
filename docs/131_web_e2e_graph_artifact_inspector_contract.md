# Web E2E Graph Artifact Inspector Contract (M16.3)

## Goal

Expose graph-run artifacts and node-output trace directly inside ReactFlow shell so developers can inspect Path/ADC/RD/RA outputs without leaving graph workspace.

Implementation:

- frontend: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
- backend dependency: graph-run summary from `/api/graph/runs/{graph_run_id}/summary`

## Scope

1. run result summary block (graph run id, shapes, counts)
2. artifact links:
   - `path_list_json`
   - `adc_cube_npz`
   - `radar_map_npz`
   - `graph_run_summary_json`
3. node-output trace from `execution.node_results`
4. visual previews:
   - `rd_map_png`
   - `ra_map_png`
   - `adc_tx0_rx0_png`
   - `path_scatter_chirp0_png`
5. absolute path normalization helper (`normalizeRepoPath`)

## UI Elements

- button: `Run Graph (API)`
- panel title: `Artifact Inspector`
- panel subsections:
  - KPI summary
  - artifact links
  - node trace
  - visuals grid

## Data Contract Expectations

Required summary fields consumed by inspector:

- `outputs.*`
- `path_summary.path_count_total`
- `adc_summary.shape`
- `radar_map_summary.rd_shape`
- `radar_map_summary.ra_shape`
- `execution.node_results[]`
- `visuals` (optional)

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
scripts/run_graph_lab_local.sh 8106 8126
curl -s "http://127.0.0.1:8106/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8126" | \
  rg -n "Run Graph \(API\)|Artifact Inspector|/api/graph/runs|visuals:|node trace:"
```

Pass criteria:

1. shell page contains run action + artifact inspector panel
2. shell references graph-run submission/summary endpoints
3. inspector text blocks for node trace and visuals are present
