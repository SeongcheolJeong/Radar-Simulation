# Web E2E Graph Contract Validation API (M16.0)

## Goal

Freeze a minimal graph contract for ReactFlow/Simulink-style pipeline editing and provide backend validation endpoint before execution-engine integration.

Implementation:

- graph contract module: `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/graph_contract.py`
- API integration: `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/web_e2e_api.py`
- validator harness: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`

## Endpoints

- `GET /api/graph/templates`
  - returns default starter graph templates
- `POST /api/graph/validate`
  - validates graph schema payload and returns normalized graph + DAG order + errors/warnings

## Request Schema (v1)

```json
{
  "version": "web_e2e_graph_schema_v1",
  "graph_id": "radar_dev_graph",
  "profile": "fast_debug",
  "nodes": [
    { "id": "scene_1", "type": "SceneSource", "params": {} }
  ],
  "edges": []
}
```

## Response Schema (v1)

```json
{
  "ok": true,
  "graph_validation": {
    "version": "web_e2e_graph_validation_v1",
    "valid": true,
    "errors": [],
    "warnings": [],
    "stats": {
      "node_count": 1,
      "edge_count": 0,
      "source_count": 1,
      "sink_count": 1
    },
    "normalized": {
      "version": "web_e2e_graph_schema_v1",
      "graph_id": "radar_dev_graph",
      "profile": "fast_debug",
      "nodes": [],
      "edges": [],
      "topological_order": []
    }
  }
}
```

## Validation Rules

1. `version` must be `web_e2e_graph_schema_v1`
2. `graph_id` required and token-safe (`[A-Za-z0-9_.:-]+`)
3. `profile` must match existing profile presets
4. node ids must be unique and token-safe
5. node type must be in allowed set
6. edge endpoints must reference existing nodes
7. graph must be DAG (cycle detection)

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. `GET /api/graph/templates` returns at least one template graph
2. `POST /api/graph/validate` succeeds for template graph (`valid=true`)
3. cycle graph sample fails validation (`valid=false`, cycle-related error exists)
