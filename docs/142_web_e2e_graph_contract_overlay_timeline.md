# Web E2E Graph Contract Overlay Timeline (M17.8)

## Goal

Add an opt-in developer overlay/timeline for contract diagnostics and attach per-run warning deltas to artifact summaries.

1. provide toggleable contract event timeline overlay
2. propagate run/gate contract delta metrics as structured runtime diagnostics
3. surface run-level contract delta in Artifact Inspector KPIs

Implementation:

- contract model/options extension:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/contracts.mjs`
- run/gate diagnostics emitters:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_graph_run_ops.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/hooks/use_gate_ops.mjs`
- app state + overlay wiring:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/app.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab_reactflow.html`

## Behavior Contract

- `GraphInputsPanel` contract model now carries:
  - `values.contractOverlayEnabled`
  - `values.contractTimelineCount`
  - `setters.setContractOverlayEnabled`
  - `contractActions.clearContractTimeline`
- run/gate hooks emit `onContractDiagnosticsEvent` payloads with:
  - `event_source`, `graph_run_id`, `timestamp_ms`
  - `baseline`, `snapshot`, `delta`
- run summary and policy eval objects include:
  - `runtime_contract_diagnostics`
- `Artifact Inspector` shows runtime delta + totals:
  - `contract_delta(unique/attempt)`
  - `contract_total(unique/attempt)`
- `ContractWarningOverlay` is opt-in (`Show Overlay`) and lists recent events.

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
scripts/run_graph_lab_local.sh 8119 8139
curl -s "http://127.0.0.1:8139/health"
curl -s "http://127.0.0.1:8119/frontend/graph_lab/app.mjs" | rg -n "ContractWarningOverlay|contractOverlayEnabled|contractTimeline|onContractDiagnosticsEvent"
curl -s "http://127.0.0.1:8119/frontend/graph_lab/contracts.mjs" | rg -n "contractOverlayEnabled|contractTimelineCount|setContractOverlayEnabled|clearContractTimeline|onContractDiagnosticsEvent"
curl -s "http://127.0.0.1:8119/frontend/graph_lab/panels.mjs" | rg -n "Show Overlay|Clear Timeline|Contract Timeline|contract_delta\\(unique/attempt\\)"
curl -s "http://127.0.0.1:8119/frontend/graph_lab/hooks/use_graph_run_ops.mjs" | rg -n "runtime_contract_diagnostics|contract_warning_delta_unique|contract_warning_delta_attempts|onContractDiagnosticsEvent"
curl -s "http://127.0.0.1:8119/frontend/graph_lab/hooks/use_gate_ops.mjs" | rg -n "runtime_contract_diagnostics|contract_warning_delta_unique|contract_warning_delta_attempts|onContractDiagnosticsEvent"
curl -s "http://127.0.0.1:8119/frontend/graph_lab_reactflow.html" | rg -n "contract-overlay|contract-overlay-row"
```

Pass criteria:

1. overlay/timeline tokens are served and toggle path is wired
2. run/gate hooks expose contract delta fields and runtime diagnostics structures
3. backend regression remains pass after frontend integration
