# Web E2E Graph Async Monitor Contract (M17.0)

## Goal

Add a practical async graph-run operator loop in Graph Lab:

1. submit graph run in sync or async mode
2. monitor async progress with polling state
3. auto-load summary on completion
4. keep cancel/retry/failure-recovery flow consistent

Implementation:

- frontend: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
- backend dependency: `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/web_e2e_api.py` (M16.5 graph run hardening API)

## UI Additions

- `Run Mode` select:
  - `sync`
  - `async`
- async poll controls:
  - `Auto Poll` checkbox
  - `poll interval ms` input
- status hint:
  - `poll_state`
  - `polling_active`
- action:
  - `Poll Last Run` button

## Behavior Contract

- run submit:
  - `Run Graph (API)` calls `POST /api/graph/runs?async=0|1` based on run mode
- async flow:
  - on async submit, run record is shown immediately
  - if `Auto Poll=true`, client polls `GET /api/graph/runs/{id}` until terminal state
  - terminal `completed` triggers summary load via `GET /api/graph/runs/{id}/summary`
  - terminal `failed|canceled` shows recovery/error details from run record
- manual flow:
  - `Poll Last Run` triggers the same polling loop for current `last_graph_run_id`
- retry flow:
  - retry endpoint call uses current run mode (`?async=0|1`)
  - async retry follows auto-poll behavior

## Validation

Backend contract regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
scripts/run_graph_lab_local.sh 8111 8131
curl -s "http://127.0.0.1:8111/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8131" | \
  rg -n "Run Mode|Auto Poll|Poll Last Run|poll_state|/api/graph/runs\\?async=|/api/graph/runs/.*/retry\\?async=|/api/graph/runs/.*/cancel"
```

Pass criteria:

1. Graph Lab contains async monitor controls/tokens
2. submit/retry paths bind to async query mode
3. polling status field and manual poll action are visible
