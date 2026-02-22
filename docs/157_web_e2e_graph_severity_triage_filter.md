# Web E2E Graph Severity-First Triage Filter (M17.24)

## Goal

Speed up incident triage by narrowing timeline rows via severity with scoped counts.

1. filter overlay rows by severity (`all/high/med/low`)
2. show scoped severity counts for quick pivots
3. preserve severity preference and align triage preset behavior

Implementation:

- severity filter state + scoped pipeline + overlay controls:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- severity filter model:
  - state: `severityFilter`
  - options: `SEVERITY_FILTER_OPTIONS` (`all`, `high`, `med`, `low`)
  - persisted in overlay prefs and restored on load
- filtering pipeline:
  - `scopedRows`: source/run/non-zero scoped rows
  - `filteredRows`: severity-applied rows from `scopedRows`
  - count display shows `filtered/scoped/all`
- triage controls:
  - select control: `co_severity_select`
  - quick buttons with counts:
    - `co_sev_btn_high`
    - `co_sev_btn_med`
    - `co_sev_btn_low`
- preset integration:
  - `Preset: Triage` sets severity to `high`
  - `Preset: Deep` / reset return severity to `all`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8155 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8135
curl -s "http://127.0.0.1:8135/frontend/graph_lab/panels.mjs" | rg -n "severityFilter|SEVERITY_FILTER_OPTIONS|co_severity_select|co_sev_btn_high|co_sev_btn_med|co_sev_btn_low|scopedRows|severityCounts|filtered/scoped/all|setSeverityFilter\\(\\\"high\\\"\\)"
```

Pass criteria:

1. severity filter state/pipeline tokens are present
2. severity filter UI/count tokens are present
3. backend regression remains pass
