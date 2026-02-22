# Web E2E Graph Policy-First Triage Filter (M17.25)

## Goal

Reduce triage time by filtering timeline rows with gate policy state after severity narrowing.

1. filter rows by policy state (`all/hold/adopt/none`)
2. expose policy quick buttons with severity-scoped counts
3. persist policy filter and align triage preset defaults

Implementation:

- policy filter state + scoped pipeline + overlay controls:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- policy filter model:
  - state: `policyFilter`
  - options: `POLICY_FILTER_OPTIONS` (`all`, `hold`, `adopt`, `none`)
  - policy classifier: `classifyPolicyState(row)` using row note gate flag
  - persisted in overlay prefs and restored on load
- filtering pipeline:
  - `scopedRows`: source/run/non-zero scope
  - `severityScopedRows`: severity-applied scope
  - `filteredRows`: policy-applied scope
  - count line shows `policy/severity/scoped/all`
- policy controls:
  - select control: `co_policy_select`
  - quick buttons with counts:
    - `co_pol_btn_hold`
    - `co_pol_btn_adopt`
    - `co_pol_btn_none`
- preset integration:
  - `Preset: Triage` sets policy to `hold`
  - deep/reset return policy to `all`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8156 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8136
curl -s "http://127.0.0.1:8136/frontend/graph_lab/panels.mjs" | rg -n "policyFilter|POLICY_FILTER_OPTIONS|classifyPolicyState|co_policy_select|co_pol_btn_hold|co_pol_btn_adopt|co_pol_btn_none|policyCounts|policy/severity/scoped/all|setPolicyFilter\\(\\\"hold\\\"\\)|setPolicyFilter\\(CONTRACT_OVERLAY_DEFAULT_PREFS\\.policyFilter\\)"
```

Pass criteria:

1. policy filter state/pipeline tokens are present
2. policy filter UI/count tokens are present
3. backend regression remains pass
