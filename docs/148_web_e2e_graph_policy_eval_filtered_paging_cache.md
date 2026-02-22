# Web E2E Graph Policy-Eval Filtered Paging + Cache (M17.15)

## Goal

Reduce repeated full-history scans when opening timeline gate evidence.

1. support filtered/paged policy-eval listing on API
2. query scoped subsets first (run/baseline) before global fallback
3. cache list responses in frontend to avoid repeated network scans

Implementation:

- API filtered paging:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/web_e2e_api.py`
- frontend API query wrapper:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/api_client.mjs`
- frontend evidence resolver cache:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`

## Behavior Contract

- `GET /api/policy-evals` supports optional query params:
  - `candidate_run_id`
  - `baseline_id`
  - `limit`
  - `offset`
- `GET /api/policy-evals` response always includes:
  - `policy_evals[]`
  - `page.total_count`
  - `page.returned_count`
  - `page.limit`
  - `page.offset`
  - `page.filtered.{candidate_run_id, baseline_id}`
- `Open Gate` fallback resolver in frontend:
  - requests scoped pages first:
    - `run_id(+baseline)` page
    - `baseline` page
    - `global` page
  - reuses cached page payloads (TTL + bounded cache)
  - emits trace fields in gate-result text:
    - `policy_eval_scan_count`
    - `policy_eval_cache_hit_any`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend/API smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8146 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8126
curl -s "http://127.0.0.1:8146/api/policy-evals?candidate_run_id=demo_run&baseline_id=demo_base&limit=10&offset=0"
curl -s "http://127.0.0.1:8126/frontend/graph_lab/app.mjs" | rg -n "fetchPolicyEvalListCached|policy_eval_cache_hit_any|run_id\\+baseline_id|candidate_run_id"
curl -s "http://127.0.0.1:8126/frontend/graph_lab/api_client.mjs" | rg -n "candidate_run_id|baseline_id|limit|offset|/api/policy-evals\\?"
```

Pass criteria:

1. API query path returns `page` metadata contract
2. frontend includes scoped-query and cache tokens
3. regression suite remains pass
