# Web E2E Graph Timeline Gate Deep-Link + Rule Badges (M17.13)

## Goal

Close operator loop from timeline rows to gate evidence while preserving per-run traceability.

1. open gate evidence from a timeline row
2. show failure-rule badges directly on timeline rows
3. keep run-jump and policy-correlation paths consistent

Implementation:

- overlay + app wiring:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
- run open action:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_graph_run_ops.mjs`
- policy metadata + gate evidence deep-link source:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`

## Behavior Contract

- overlay rows expose two actions:
  - `Open Run`: opens run summary/record and pins run filter
  - `Open Gate`: opens gate evidence summary in `Policy Gate Result`
- policy badges:
  - correlation badge: `policy:HOLD#N` / `policy:ADOPT`
  - rule badge class: `contract-failure-rule-badge`
- gate note fields include:
  - `policy_eval_id`, `recommendation`
  - `failure_count`, `failure_rules[]`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
scripts/run_graph_lab_local.sh 8123 8143
curl -s "http://127.0.0.1:8143/health"
curl -s "http://127.0.0.1:8123/frontend/graph_lab/hooks/use_graph_run_ops.mjs" | rg -n "openGraphRunById|graph_run_overlay_open|opened_from_overlay"
curl -s "http://127.0.0.1:8123/frontend/graph_lab/app.mjs" | rg -n "onOpenRun|onOpenGateEvidence"
curl -s "http://127.0.0.1:8123/frontend/graph_lab/panels.mjs" | rg -n "Open Run|Open Gate|getFailureRuleTags|contract-policy-tag|contract-failure-rule-badge"
curl -s "http://127.0.0.1:8123/frontend/graph_lab_reactflow.html" | rg -n "contract-policy-tag|contract-failure-rule-badge|contract-open-gate-btn"
curl -s "http://127.0.0.1:8123/frontend/graph_lab/hooks/use_gate_ops.mjs" | rg -n "failure_rules|failure_count|\\| policy=|## Contract Timeline Tail"
```

Pass criteria:

1. row-level run/gate deep-link tokens are present
2. policy + failure-rule badges are present in timeline rendering
3. regression suite remains pass
