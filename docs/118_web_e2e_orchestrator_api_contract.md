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
- `GET /api/comparisons`
- `GET /api/comparisons/{comparison_id}`
- `POST /api/compare`

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

## POST /api/compare Request

```json
{
  "reference_run_id": "run_20260222_123000_abcd1234",
  "candidate_run_id": "run_20260222_123045_efgh5678",
  "thresholds": {
    "rd_shape_nmse_max": 0.25,
    "ra_shape_nmse_max": 0.25
  }
}
```

`POST /api/compare` rules:

- compare target must provide one of:
  - `reference_run_id` or `reference_summary_json`
  - `candidate_run_id` or `candidate_summary_json`
- thresholds are optional and override default parity thresholds

`POST /api/compare` response:

- `comparison.version` = `web_e2e_compare_v1`
- `comparison.reference` / `comparison.candidate`
  - `run_id` (nullable when summary-json mode)
  - `run_summary_json`
  - `radar_map_npz`
- `comparison.parity` (shared `avxsim.parity` metrics/failures)
- `comparison.verdict.pass` and `comparison.verdict.failure_count`

`POST /api/runs` rules:

- `scene_json_path` required
- `profile` one of: `fast_debug`, `balanced_dev`, `fidelity_eval`
- `output_subdir` must be safe relative path

## Run Storage Layout

- `<store_root>/runs/<run_id>/run_record.json`
- `<store_root>/runs/<run_id>/run_summary.json`
- `<store_root>/runs/<run_id>/output/` (pipeline artifacts)
- `<store_root>/comparisons/<comparison_id>.json`

## Run Summary (v2)

`GET /api/runs/{run_id}/summary` now returns a frontend-compatible schema:

- run metadata:
  - `version`, `run_id`, `status`, `profile`, `created_at`, `completed_at`, `request`
- scene/artifact paths:
  - `scene_json`
  - `outputs.path_list_json`
  - `outputs.adc_cube_npz`
  - `outputs.radar_map_npz`
  - `outputs.hybrid_estimation_npz` (optional)
  - `outputs.run_summary_json`
- summaries:
  - `path_summary` (`n_chirps`, `path_count_total`, `path_count_per_chirp`, `first_chirp_paths`)
  - `adc_summary` (`shape`, `dtype`, `abs_mean`, `abs_max`, `metadata`)
  - `radar_map_summary` (`rd_shape`, `ra_shape`, top peaks, metadata)
- compatibility:
  - `quicklook` retained for phase-0 clients
  - `artifacts` mirrors `outputs`

## Start API

```bash
cd /Users/seongcheoljeong/Documents/Codex_test
PYTHONPATH=src python3 scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8099
```

One-command local dashboard + API launcher:

```bash
scripts/run_web_e2e_dashboard_local.sh 8080 8099
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
4. Run summary endpoint returns frontend-compatible v2 summary fields and expected shapes
5. Run list contains created `run_id`
6. Compare endpoint returns parity verdict and persisted comparison entry

Notes:

- `visuals` is best-effort and may be omitted if plotting dependency is unavailable in the runtime python.
