# Web E2E Graph Historical Policy-Eval Fetch (M17.14)

## Goal

Harden `Open Gate` so timeline rows can open persisted gate evidence even when local in-memory `lastPolicyEval` is stale/missing.

1. resolve policy evidence from `/api/policy-evals/{policy_eval_id}` first
2. fallback to `/api/policy-evals` list scan using run/summary hints
3. surface which evidence path was used to keep operator traceability

Implementation:

- API client wrappers:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/api_client.mjs`
- timeline gate-evidence resolver:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
- timeline event metadata source:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`

## Behavior Contract

- `Open Gate` in contract overlay now runs async resolution path:
  - direct fetch: `GET /api/policy-evals/{policy_eval_id}`
  - fallback scan: `GET /api/policy-evals`
- fallback matching order:
  - `policy_eval_id`
  - `candidate.run_id + candidate.run_summary_json`
  - `candidate.run_id`
  - `candidate.run_summary_json`
  - `baseline.baseline_id`
- `Policy Gate Result` now includes:
  - `evidence_source: persisted/...` (or `timeline_note_only`)
  - `policy_eval_scan_count`
- gate timeline note includes:
  - `candidate_run_id`
  - `candidate_summary_json`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
scripts/run_graph_lab_local.sh 8124 8144
curl -s "http://127.0.0.1:8144/health"
curl -s "http://127.0.0.1:8124/frontend/graph_lab/app.mjs" | rg -n "listPolicyEvals|getPolicyEval|policy_eval_list:run_id|evidence_source: persisted|gate evidence unresolved"
curl -s "http://127.0.0.1:8124/frontend/graph_lab/api_client.mjs" | rg -n "/api/policy-evals|listPolicyEvals|getPolicyEval"
curl -s "http://127.0.0.1:8124/frontend/graph_lab/hooks/use_gate_ops.mjs" | rg -n "candidate_run_id|candidate_summary_json"
```

Pass criteria:

1. direct and fallback policy-eval resolution tokens are present
2. timeline note contains run/summary hints for fallback
3. backend regression remains pass
