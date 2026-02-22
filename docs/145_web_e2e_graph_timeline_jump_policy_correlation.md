# Web E2E Graph Timeline Jump + Policy Correlation (M17.11/M17.12)

## Goal

Make contract timeline rows actionable for operators and automatically correlate rows with policy gate outcomes.

1. support row-level jump from timeline to graph-run view
2. support row-level deep-link from timeline to gate evidence summary
3. attach policy correlation tags (`HOLD/ADOPT`) and rule badges on timeline rows
4. carry policy correlation into gate report timeline-tail references

Implementation:

- run-jump action:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_graph_run_ops.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
- policy correlation tags:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
- policy metadata + report tail:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`

## Behavior Contract

- `useGraphRunOps` exports `openGraphRunById(graph_run_id)`:
  - if `completed` -> loads summary via existing summary path
  - otherwise -> renders run record text and status
- `ContractWarningOverlay` row actions:
  - `Open Run` button per row (when `graph_run_id` exists)
  - clicking pins `run` filter and calls `onOpenRun(graph_run_id)`
  - `Open Gate` button per row (when policy correlation exists)
  - clicking calls `onOpenGateEvidence(row)` and updates `Policy Gate Result`
- timeline policy-correlation tag format:
  - `policy:HOLD#<failure_count>`
  - `policy:ADOPT`
- timeline failure-rule badges:
  - rendered from `failure_rules[]` as `contract-failure-rule-badge`
- policy event note enrichment:
  - `policy_eval_id`
  - `recommendation`
  - `failure_count`
  - `failure_rules[]` (top rules)
- gate report timeline tail (`## Contract Timeline Tail`) includes:
  - `policy:...` correlation token in each tail line

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
scripts/run_graph_lab_local.sh 8122 8142
curl -s "http://127.0.0.1:8142/health"
curl -s "http://127.0.0.1:8122/frontend/graph_lab/hooks/use_graph_run_ops.mjs" | rg -n "openGraphRunById|opening graph run|graph_run_overlay_open|opened_from_overlay"
curl -s "http://127.0.0.1:8122/frontend/graph_lab/app.mjs" | rg -n "openGraphRunById|onOpenRun|onOpenGateEvidence"
curl -s "http://127.0.0.1:8122/frontend/graph_lab/panels.mjs" | rg -n "Open Run|Open Gate|getPolicyCorrelationTag|getFailureRuleTags|policy:HOLD#|policy:ADOPT|contract-policy-tag|contract-failure-rule-badge"
curl -s "http://127.0.0.1:8122/frontend/graph_lab_reactflow.html" | rg -n "contract-policy-tag|contract-failure-rule-badge|contract-open-gate-btn"
curl -s "http://127.0.0.1:8122/frontend/graph_lab/hooks/use_gate_ops.mjs" | rg -n "failure_rules|failure_count|\\| policy=|## Contract Timeline Tail"
```

Pass criteria:

1. row jump tokens and callbacks are present
2. gate deep-link tokens and callbacks are present
3. policy correlation tags + rule badges are rendered on timeline rows
4. gate report timeline-tail lines include policy correlation token
