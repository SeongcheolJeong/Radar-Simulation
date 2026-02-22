# Web E2E Graph Action Hooks Split Contract (M17.3)

## Goal

Split Graph Lab run/gate action logic from `app.mjs` into dedicated hooks so the app keeps state orchestration while side-effect heavy flows are isolated.

1. move graph run actions to `useGraphRunOps`
2. move baseline/gate actions to `useGateOps`
3. preserve M16.5/M17.0 behavior (async polling, retry/cancel, gate/report)

Implementation:

- app orchestration: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
- run hook: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_graph_run_ops.mjs`
- gate hook: `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`

## Behavior Contract

- `app.mjs` does not implement raw run/gate action bodies; it calls hooks.
- `useGraphRunOps` provides:
  - `runGraphViaApi`
  - `retryLastGraphRun`
  - `cancelLastGraphRun`
  - `pollLastGraphRunOnce`
- `useGateOps` provides:
  - `pinBaselineFromGraphRun`
  - `runPolicyGateForGraphRun`
  - `exportGateReport`
- Existing endpoint semantics remain unchanged:
  - run/retry query includes `?async=...`
  - cancel endpoint remains enabled
  - baseline/policy endpoints remain unchanged

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
scripts/run_graph_lab_local.sh 8114 8134
curl -s "http://127.0.0.1:8114/frontend/graph_lab/app.mjs" | rg -n "useGraphRunOps|useGateOps|runGraphViaApi|runPolicyGateForGraphRun"
curl -s "http://127.0.0.1:8114/frontend/graph_lab/hooks/use_graph_run_ops.mjs" | rg -n "runGraph\(|retryGraphRun\(|cancelGraphRun\(|getGraphRunSummaryMaybe\(|\?async="
curl -s "http://127.0.0.1:8114/frontend/graph_lab/hooks/use_gate_ops.mjs" | rg -n "createBaseline\(|evaluatePolicyGate\(|graph_gate_report_"
```

Pass criteria:

1. hook modules are served and referenced by app
2. M16.5/M17.0 control paths still resolve to same API endpoint contracts
3. API regression validator remains pass
