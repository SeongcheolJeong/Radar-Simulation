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
- `GET /api/baselines`
- `GET /api/baselines/{baseline_id}`
- `POST /api/baselines`
- `GET /api/policy-evals`
- `GET /api/policy-evals/{policy_eval_id}`
- `POST /api/compare/policy`
- `GET /api/regression-sessions`
- `GET /api/regression-sessions/{session_id}`
- `POST /api/regression-sessions`
- `GET /api/regression-exports`
- `GET /api/regression-exports/{export_id}`
- `POST /api/regression-exports`

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

## POST /api/baselines Request

```json
{
  "baseline_id": "main_baseline",
  "run_id": "run_20260222_123000_abcd1234",
  "overwrite": true,
  "note": "baseline pinned from dashboard"
}
```

Rules:

- `baseline_id` required (`[A-Za-z0-9_.-]{1,128}`)
- source must provide one of: `run_id` or `summary_json`

## POST /api/compare/policy Request

```json
{
  "baseline_id": "main_baseline",
  "candidate_run_id": "run_20260222_123045_efgh5678",
  "policy": {
    "require_parity_pass": true,
    "max_failure_count": 0,
    "max_rd_shape_nmse": 0.25,
    "max_ra_shape_nmse": 0.25
  }
}
```

Rules:

- baseline source is either:
  - `baseline_id` (preferred), or
  - `reference_run_id` / `reference_summary_json`
- candidate source is one of:
  - `candidate_run_id`
  - `candidate_summary_json`
- if `policy` omitted, server default policy is used

Response:

- `policy_eval.version` = `web_e2e_compare_policy_v1`
- `policy_eval.policy_eval_id`
- `policy_eval.baseline` / `policy_eval.candidate`
- `policy_eval.parity`
- `policy_eval.gate_failed`
- `policy_eval.gate_failures`
- `policy_eval.recommendation` (`adopt_candidate` or `hold_candidate`)

## POST /api/regression-sessions Request

```json
{
  "session_id": "main_regression",
  "baseline_id": "main_baseline",
  "candidate_run_ids": [
    "run_20260222_123045_efgh5678",
    "run_20260222_123120_ijkl9012"
  ],
  "stop_on_first_fail": false,
  "policy": {
    "require_parity_pass": true,
    "max_failure_count": 0
  }
}
```

Rules:

- baseline source is either:
  - `baseline_id` (preferred), or
  - `reference_run_id` / `reference_summary_json`
- candidate set is provided by one or more:
  - `candidate_run_ids: string[]`
  - `candidate_summary_jsons: string[]`
  - `candidates: [{run_id|summary_json,label?}]`
- duplicates are removed by `(run_id, summary_json)` key
- `stop_on_first_fail=true` truncates evaluation at first hold case

Response:

- `regression_session.version` = `web_e2e_regression_session_v1`
- `regression_session.session_id`
- `regression_session.requested_candidate_count`
- `regression_session.evaluated_candidate_count`
- `regression_session.adopted_count`
- `regression_session.held_count`
- `regression_session.truncated`
- `regression_session.recommendation`
- `regression_session.rows[]` (per-candidate policy verdict summaries)

## POST /api/regression-exports Request

```json
{
  "session_id": "main_regression",
  "export_id": "main_regression_export",
  "include_policy_payload": true
}
```

Rules:

- `session_id` is required and must reference existing regression session
- `export_id` is optional (auto-generated if omitted)
- `overwrite=true` replaces existing export with same `export_id`
- export emits artifacts:
  - `regression_session.json` (session snapshot)
  - `regression_rows.csv` (rows tabular view)
  - `regression_summary_index.json` (candidate/policy summary index)
  - `regression_package.json` (JSON package for downstream consumers)

Response:

- `regression_export.version` = `web_e2e_regression_export_v1`
- `regression_export.export_id`
- `regression_export.session_id`
- `regression_export.row_count`
- `regression_export.include_policy_payload`
- `regression_export.artifacts.artifact_dir`
- `regression_export.artifacts.session_json`
- `regression_export.artifacts.rows_csv`
- `regression_export.artifacts.summary_index_json`
- `regression_export.artifacts.package_json`

`POST /api/runs` rules:

- `scene_json_path` required
- `profile` one of: `fast_debug`, `balanced_dev`, `fidelity_eval`
- `output_subdir` must be safe relative path

## Run Storage Layout

- `<store_root>/runs/<run_id>/run_record.json`
- `<store_root>/runs/<run_id>/run_summary.json`
- `<store_root>/runs/<run_id>/output/` (pipeline artifacts)
- `<store_root>/comparisons/<comparison_id>.json`
- `<store_root>/baselines/<baseline_id>.json`
- `<store_root>/policy_evals/<policy_eval_id>.json`
- `<store_root>/regression_sessions/<session_id>.json`
- `<store_root>/regression_exports/<export_id>.json`
- `<store_root>/regression_exports/<export_id>/` (`regression_session.json`, `regression_rows.csv`, `regression_summary_index.json`, `regression_package.json`)

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

```bash
curl -s -X POST "http://127.0.0.1:8099/api/baselines" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_id":"main_baseline",
    "run_id":"run_20260222_123000_abcd1234",
    "overwrite":true
  }' | jq .
```

```bash
curl -s -X POST "http://127.0.0.1:8099/api/compare/policy" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_id":"main_baseline",
    "candidate_run_id":"run_20260222_123045_efgh5678"
  }' | jq .
```

```bash
curl -s -X POST "http://127.0.0.1:8099/api/regression-sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id":"main_regression",
    "baseline_id":"main_baseline",
    "candidate_run_ids":[
      "run_20260222_123045_efgh5678",
      "run_20260222_123120_ijkl9012"
    ],
    "stop_on_first_fail":false
  }' | jq .
```

```bash
curl -s -X POST "http://127.0.0.1:8099/api/regression-exports" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id":"main_regression",
    "export_id":"main_regression_export",
    "include_policy_payload":true
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
7. Baseline pin endpoint stores/retrieves pinned baseline
8. Compare policy endpoint returns persisted policy verdict payload
9. Regression session endpoint returns batch verdict summary and persisted session payload
10. Regression export endpoint writes CSV/JSON artifacts and returns persisted export manifest

Notes:

- `visuals` is best-effort and may be omitted if plotting dependency is unavailable in the runtime python.
