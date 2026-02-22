# Web E2E Graph Overlay Gate-History Window + Incremental Lookup (M17.16)

## Goal

Make gate-evidence lookup knobs explicit in the overlay and support incremental page-budget search for large histories.

1. expose lookup controls directly where `Open Gate` is used
2. let users widen search gradually without global hardcoded limits
3. keep evidence trace output explicit for reproducibility

Implementation:

- overlay controls + row action payload:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
- lookup resolver incremental paging:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`

## Behavior Contract

- Contract overlay filter row adds:
  - `gate window` selector
  - `max pages` selector
  - `+page` quick-increment button
- `Open Gate` now calls resolver with lookup options:
  - `historyLimit`
  - `pageBudget`
- resolver behavior:
  - scopes: `run_id(+baseline)` -> `baseline` -> `global`
  - per-scope page loop: `offset = page_idx * historyLimit`
  - stop conditions: match found, end reached, or `pageBudget` exhausted
- `Policy Gate Result` traces:
  - `policy_eval_history_limit`
  - `policy_eval_page_budget`
  - `policy_eval_page_count_used`
  - `policy_eval_scan_count`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend/API smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8147 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8127
curl -s "http://127.0.0.1:8147/api/policy-evals?candidate_run_id=demo_run&baseline_id=demo_base&limit=64&offset=128"
curl -s "http://127.0.0.1:8127/frontend/graph_lab/app.mjs" | rg -n "historyLimit|pageBudget|policy_eval_page_budget|policy_eval_page_count_used|@page"
curl -s "http://127.0.0.1:8127/frontend/graph_lab/panels.mjs" | rg -n "gate window|max pages|co_gate_window_select|co_gate_pages_select|\\+page|gateOpenHandler\\(row, gateLookupOptions\\)"
```

Pass criteria:

1. overlay controls and `Open Gate` option pass-through tokens are present
2. resolver paging tokens and trace fields are present
3. backend regression remains pass
