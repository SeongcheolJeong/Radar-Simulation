# Web E2E Graph Contract Compact Pin + Tail Ref (M17.10)

## Goal

Add operator-focused compact timeline mode and include timeline tail references in gate report exports.

1. compact overlay mode with severity badges
2. pin timeline to a selected graph run id
3. append timeline tail references to exported gate markdown

Implementation:

- overlay UI behavior:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`
- gate report enrichment:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`
- gate options contract + app wiring:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/contracts.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`

## Behavior Contract

- `ContractWarningOverlay` now supports:
  - compact toggle (`Compact: on/off`)
  - run pin filter (`run:` select)
  - severity classification (`HIGH/MED/LOW`) with badge + row style
- severity rule:
  - `high`: error/failure events
  - `med`: cancel/gate-failed/delta increase
  - `low`: no failure/delta growth
- `useGateOps.exportGateReport()` now adds:
  - `## Contract Timeline Tail`
  - `active_graph_run_id`, `scoped_event_count`, `tail_event_count`
  - timeline references (`t/source/run/sev/delta`)
  - export hint (`Contract Overlay -> Export JSON`)
- `normalizeGateOpsOptions()` now accepts:
  - `contractTimeline` array option

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
scripts/run_graph_lab_local.sh 8121 8141
curl -s "http://127.0.0.1:8141/health"
curl -s "http://127.0.0.1:8121/frontend/graph_lab/panels.mjs" | rg -n "Compact: on|Compact: off|run:|pinnedRunId|classifyContractSeverity|contract-sev-badge|contract-overlay-row-compact"
curl -s "http://127.0.0.1:8121/frontend/graph_lab_reactflow.html" | rg -n "contract-sev-badge|contract-sev-high|contract-overlay-row-compact"
curl -s "http://127.0.0.1:8121/frontend/graph_lab/hooks/use_gate_ops.mjs" | rg -n "## Contract Timeline Tail|timeline_export_hint|tail_event_count|scoped_event_count|formatTimelineRefLine|sev="
curl -s "http://127.0.0.1:8121/frontend/graph_lab/contracts.mjs" | rg -n "contractTimeline: readArray\\(scope, root, \\\"contractTimeline\\\""
curl -s "http://127.0.0.1:8121/frontend/graph_lab/app.mjs" | rg -n "contractTimeline,"
```

Pass criteria:

1. compact/pinned/severity overlay tokens are present
2. gate report timeline-tail section tokens are present
3. backend regression remains pass
