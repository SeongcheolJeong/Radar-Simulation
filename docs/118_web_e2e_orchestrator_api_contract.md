# Web E2E Orchestrator API Contract (Phase 0)

## Goal

Provide a minimal web API that wraps existing scene pipeline execution and exposes run lifecycle records.

Implementation:

- module: `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/web_e2e_api.py`
- run script: `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py`
- validation: `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`

## Endpoints

- `GET /health`
- `GET /api/profiles`
- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/summary`
- `POST /api/runs?async=1|0`

## POST /api/runs Request

```json
{
  "scene_json_path": "data/demo/frontend_quickstart_v1/scene_frontend_quickstart.json",
  "profile": "fast_debug",
  "run_hybrid_estimation": false,
  "output_subdir": "output",
  "tag": "dev_trial"
}
```

Rules:

- `scene_json_path` required
- `profile` one of: `fast_debug`, `balanced_dev`, `fidelity_eval`
- `output_subdir` must be safe relative path

## Run Storage Layout

- `<store_root>/runs/<run_id>/run_record.json`
- `<store_root>/runs/<run_id>/run_summary.json`
- `<store_root>/runs/<run_id>/output/` (pipeline artifacts)

## Run Summary (v1)

Contains:

- request snapshot
- artifact paths (`path_list`, `adc_cube`, `radar_map`)
- quicklook metrics:
  - `n_chirps`, `path_count_total`
  - `adc_shape`, `rd_shape`, `ra_shape`
  - top RD/RA peaks

## Start API

```bash
cd /Users/seongcheoljeong/Documents/Codex_test
PYTHONPATH=src python3 scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8099
```

## Example Calls

```bash
curl -s http://127.0.0.1:8099/health | jq .
curl -s http://127.0.0.1:8099/api/profiles | jq .
```

```bash
curl -s -X POST "http://127.0.0.1:8099/api/runs?async=0" \
  -H "Content-Type: application/json" \
  -d '{
    "scene_json_path":"data/demo/frontend_quickstart_v1/scene_frontend_quickstart.json",
    "profile":"fast_debug",
    "run_hybrid_estimation":false
  }' | jq .
```

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. Health endpoint returns `ok=true`
2. Profile endpoint returns three presets
3. Sync run creation completes with `status=completed`
4. Run summary endpoint returns quicklook with expected shapes
5. Run list contains created `run_id`
