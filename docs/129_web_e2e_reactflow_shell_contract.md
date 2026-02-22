# Web E2E ReactFlow Shell Contract (M16.1)

## Goal

Provide a usable ReactFlow-based graph shell that allows template loading, graph editing, node parameter inspection, and graph-contract validation from the browser.

Implementation:

- frontend shell: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
- local launcher: `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_graph_lab_local.sh`
- backend dependencies:
  - `GET /api/graph/templates`
  - `POST /api/graph/validate`

## Functional Scope

1. graph canvas (node drag + edge connect)
2. node palette (add v1 node types)
3. template load from API
4. selected-node params JSON editor
5. graph validation request/result rendering
6. graph export as `web_e2e_graph_schema_v1` JSON

## URL

```text
/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:<api_port>
```

## Validation

```bash
scripts/run_graph_lab_local.sh 8104 8124
curl -s http://127.0.0.1:8124/health
curl -s "http://127.0.0.1:8104/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8124" | \
  rg -n "Radar Graph Lab|@xyflow/react|/api/graph/templates|/api/graph/validate|Validate Graph Contract|Node Inspector"
```

Pass criteria:

1. shell HTML served and contains ReactFlow integration tokens
2. shell references graph-template and graph-validation endpoints
3. launcher starts API + static server and health endpoint returns `ok=true`
