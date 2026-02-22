# Web E2E Graph Contract Timeline Filter + Export (M17.9)

## Goal

Improve developer workflow around contract diagnostics by adding timeline filtering/export and including contract delta slices in gate handoff reports.

1. filter overlay timeline events by source and non-zero deltas
2. export contract timeline JSON bundle for offline review
3. include run/gate contract diagnostics section in gate markdown report

Implementation:

- overlay controls:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
- export action wiring:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
- report enrichment:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`

## Behavior Contract

- `ContractWarningOverlay` adds:
  - source filter (`source:` select)
  - non-zero delta filter (`non-zero delta`)
  - event count indicator (`showing filtered/total`)
  - `Export JSON` button
- `app.mjs` exports:
  - `contract_timeline_export_v1` JSON payload
  - fields: `exported_at_utc`, `event_count`, `events[]`
- gate report markdown includes:
  - `## Contract Diagnostics`
  - `contract_debug_version`
  - run/gate delta and total slices (`run.*`, `gate.*`)

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
scripts/run_graph_lab_local.sh 8120 8140
curl -s "http://127.0.0.1:8140/health"
curl -s "http://127.0.0.1:8120/frontend/graph_lab/app.mjs" | rg -n "exportContractTimeline|contract_timeline_export_v1|onExport"
curl -s "http://127.0.0.1:8120/frontend/graph_lab/panels.mjs" | rg -n "Export JSON|source:|non-zero delta|showing .*\\/|contract-overlay-filter"
curl -s "http://127.0.0.1:8120/frontend/graph_lab/hooks/use_gate_ops.mjs" | rg -n "## Contract Diagnostics|runtime_contract_diagnostics|run\\.delta_unique|gate\\.delta_unique|contract_debug_version"
curl -s "http://127.0.0.1:8120/frontend/graph_lab_reactflow.html" | rg -n "contract-overlay-filter"
```

Pass criteria:

1. overlay filtering/export tokens are present and wired
2. gate report markdown includes contract diagnostics block
3. backend regression remains pass
