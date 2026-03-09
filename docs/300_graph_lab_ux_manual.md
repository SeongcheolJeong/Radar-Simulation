# Graph Lab UX Manual

## Purpose

This manual explains how to use the main frontend operator UI in `frontend/graph_lab`.

Use it when you want to:

- recognize the main screen areas quickly
- understand what the main buttons do
- run the frontend against the backend
- perform the standard low-vs-high comparison flow
- know what a healthy frontend/backend connection looks like

This document focuses on `Graph Lab`.

For the lightweight demo shell, use [Frontend Dashboard Usage](116_frontend_dashboard_usage.md).

If you want the shortest click-by-click checklist while the UI is open, use [Graph Lab Live Checklist](306_graph_lab_live_checklist.md).

If you are not sure which Graph Lab document to open first, use [Graph Lab Document Map](322_graph_lab_doc_map.md).

If you need a failure-first reading flow, use [Graph Lab Failure Reading Guide](324_graph_lab_failure_reading_guide.md).

## Start Graph Lab

Run:

```bash
PY_BIN=.venv/bin/python scripts/run_graph_lab_local.sh 8081 8101
```

Open:

- `http://127.0.0.1:8081/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8101`

Quick backend health check:

```bash
curl http://127.0.0.1:8101/health
```

Healthy first sign:

- the page loads
- the canvas is visible
- the left and right side panels render
- `Run Graph (API)` returns a new `graph_run_id`

## Screen Map

Full layout:

![Graph Lab full layout](reports/graph_lab_playwright_snapshots/latest/page_full.png)

Annotated layout:

![Graph Lab full layout annotated](reports/graph_lab_playwright_snapshots/latest/page_full_annotated.png)

Main areas:

1. Left panel
   - graph setup
   - runtime configuration
   - template loading
   - graph execution
2. Center canvas
   - graph nodes and edges
   - scene/synth/map flow visualization
3. Right panel
   - `Decision Pane`
   - `Artifact Inspector`
   - compare state and export actions

Left panel example:

![Graph Lab left panel](reports/graph_lab_playwright_snapshots/latest/left_panel.png)

Decision Pane example:

![Decision Pane](reports/graph_lab_playwright_snapshots/latest/decision_pane.png)

Annotated Decision Pane:

![Decision Pane annotated](reports/graph_lab_playwright_snapshots/latest/decision_pane_annotated.png)

Artifact Inspector example:

![Artifact Inspector](reports/graph_lab_playwright_snapshots/latest/artifact_inspector.png)

If you only need the practical reading order for the right panel, use [Artifact Inspector Quick Guide](304_artifact_inspector_quick_guide.md).

Annotated Artifact Inspector:

![Artifact Inspector annotated](reports/graph_lab_playwright_snapshots/latest/artifact_inspector_annotated.png)

## Left Panel: Graph Setup And Runtime

### Graph Setup Buttons

| Button | Use it when | Result |
| --- | --- | --- |
| `Load #1` | you want a known-good starting graph | loads the first template into the canvas |
| node chips in `Node Palette` | you want to add nodes manually | adds a node of the selected type |
| `Validate Graph Contract` | before any backend run | checks schema/profile/DAG constraints |
| `Run Graph (API)` | the graph is ready | sends the current graph to the backend |
| `Retry Last Run` | the last API run failed transiently | resubmits the last run |
| `Cancel Last Run` | an async or long run should stop | asks the backend to stop the last run |
| `Poll Last Run` | you want a fresh status without rerunning | refreshes the last run state |
| `Refresh Guard` | contract overlay state looks stale | refreshes contract diagnostics |
| `Reset Guard` | contract diagnostics should be cleared | clears current guard state |
| `Clear Timeline` | contract overlay history is noisy | clears overlay timeline rows |

### Runtime Panel

The runtime panel is the main frontend control surface for backend selection.

Most important controls:

| Control | Purpose |
| --- | --- |
| `Low Fidelity: RadarSimPy + FFD` | quick baseline path using RadarSimPy-style runtime |
| `High Fidelity: Sionna-style RT` | optional Sionna-style ray-tracing path |
| `High Fidelity: PO-SBR` | higher-fidelity PO-SBR path |
| `Runtime Backend` | actual backend family to run |
| `Runtime Provider (module:function)` | exact provider entry point |
| `Runtime Required Modules` | required Python/runtime modules |
| `Failure Policy` | fail hard or fall back |
| `Simulation Mode` | select analytic path or RadarSimPy ADC path |
| `Multiplexing Mode` | `tdm`, `bpm`, or `custom` |
| `License Tier` | `trial` or `production` |
| `License File` | explicit paid runtime `.lic` path |
| `TX FFD Files` / `RX FFD Files` | antenna pattern inputs |
| `Runtime Diagnostics` | planned and observed backend state summary |

### Runtime Preset Meaning

| Preset | Typical use |
| --- | --- |
| `Low Fidelity: RadarSimPy + FFD` | fast baseline and compare reference |
| `High Fidelity: Sionna-style RT` | optional ray-tracing-oriented path |
| `High Fidelity: PO-SBR` | full PO-SBR closure path; can be long-running |

When `PO-SBR` is selected, read the warning under `Purpose Presets`:

- use `.venv-po-sbr`
- expect Linux + NVIDIA
- prefer `Sionna-style RT` for interactive checks
- verify the current runtime verdict in [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json)

If you want the backend execution sequence behind these presets, read [Graph Lab Low/High Fidelity Execution Flow](338_graph_lab_low_high_fidelity_execution_flow.md).

### Multiplexing Controls

| Mode | Use it when |
| --- | --- |
| `tdm` | standard FMCW-TDM path |
| `bpm` | you want BPM phase coding |
| `custom` | you want explicit JSON pulse amplitude/phase control |

## Right Panel: Decision Pane

The `Decision Pane` is where compare, gate, session, and export actions happen.

If you want a shorter read focused only on this area, use [Decision Pane Quick Guide](326_graph_lab_decision_pane_quick_guide.md).

### Compare Buttons

| Button | Use it when | Result |
| --- | --- | --- |
| `Load Compare` | you already know a `graph_run_id` to compare against | loads that run as compare reference |
| `Use Current as Compare` | the current run should become the reference | pins the current run as compare |
| `Clear Compare` | you want to remove the current compare reference | resets compare state |
| `Run Preset Pair Compare` | you want a baseline and target pair executed in order | runs `baseline_preset -> target_preset` |
| `Run Low -> Current Compare` | you want the default low-vs-current fast path | builds a low-fidelity baseline and then runs the current config |

### Inspector Mirror Buttons

These buttons control the `Artifact Inspector` from the `Decision Pane`.

| Button | Result |
| --- | --- |
| `Collapse Inspector Evidence` | hides inspector detail sections |
| `Expand Inspector Evidence` | reopens inspector detail sections |
| `Reset Inspector Layout` | returns inspector fold/layout state to defaults |
| `Apply Recommended Audit Action` | applies the suggested audit maintenance action |
| `Clear Action Trail` | clears inspector action audit history |
| `Clear Maintenance Marker` | clears maintenance marker state |
| `Clear Last Clear Record` | clears retained clear-provenance record |

### Decision And Export Buttons

| Button | Use it when | Result |
| --- | --- | --- |
| `Policy Gate` | current-vs-compare pair is ready for decision | computes gate result |
| `Run Session` | you want a decision/regression session record | records a session |
| `Export Session` | you want the session artifact | downloads or exports the current session summary |
| `Export Gate` | you want the gate evidence package | downloads or exports gate evidence |
| `Export Brief` | you want a stakeholder-facing summary | exports the decision brief markdown |

### Compare History Area

The lower `Compare Session History` area becomes useful after at least one compare run.

Main functions:

- replay old compare pairs
- pin important pairs
- rename saved pairs
- delete stale pairs
- export and import compare history bundles
- control retention policy

If you need the exact compare-history behavior, use [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md).

## Right Panel: Artifact Inspector

The `Artifact Inspector` is the evidence panel.

For a shorter read focused only on this panel, use [Artifact Inspector Quick Guide](304_artifact_inspector_quick_guide.md).

For the compare, gate, session, and export controls above it, use [Decision Pane Quick Guide](326_graph_lab_decision_pane_quick_guide.md).

Use it to check:

- current artifact presence
- compare-vs-current evidence
- shape, path, and peak-bin drift
- runtime source changes
- audit and maintenance state

Local panel buttons:

| Button | Result |
| --- | --- |
| `Apply Recommended Audit Action` | applies recommended audit cleanup |
| `Clear Action Trail` | clears retained action audit trail |
| `Clear Maintenance Marker` | clears maintenance marker state |
| `Clear Last Clear Record` | clears last-clear provenance state |

Healthy signs in this panel:

- current and compare artifacts both exist
- compare assessment is not unexpectedly degraded
- `Runtime Diagnostics` and artifact evidence agree
- audit state is understandable and not stale

## Recommended Run Sequences

### Sequence 1: First Frontend/Backend Sanity Check

Use this when you want to prove the UI is alive and connected.

1. Start Graph Lab with `scripts/run_graph_lab_local.sh 8081 8101`.
2. Open the URL.
3. Click `Load #1`.
4. Click `Validate Graph Contract`.
5. In the runtime panel, click `Low Fidelity: RadarSimPy + FFD`.
6. Click `Run Graph (API)`.
7. Confirm:
   - a new `graph_run_id` appears
   - `Runtime Diagnostics` shows a concrete backend/provider state
   - the right panel fills with current artifact information

### Sequence 2: Low-Vs-High Compare

Use this when you want the standard operator workflow.

1. Run a low-fidelity baseline:
   - click `Low Fidelity: RadarSimPy + FFD`
   - click `Run Graph (API)`
2. Pin it as compare:
   - click `Use Current as Compare`
3. Switch to the target high-fidelity path:
   - click `High Fidelity: Sionna-style RT`
   - or click `High Fidelity: PO-SBR`
   - if uncertain, verify the current recommendation in [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json)
4. Fill any required advanced runtime inputs if the preset leaves them incomplete.
5. Click `Run Graph (API)` again.
6. Read:
   - `Track Compare Workflow`
   - `Preset Pair Compare`
   - `Artifact Inspector`
7. If the pair is final, click `Policy Gate`.
8. Then click `Run Session` and `Export Brief`.

If you want to understand what happens internally during this sequence, read [Graph Lab Low/High Fidelity Execution Flow](338_graph_lab_low_high_fidelity_execution_flow.md).

Fast path:

1. Set the target runtime you want.
2. Click `Run Low -> Current Compare`.
3. Read the compare evidence after the automatic pair run.

### Sequence 3: Preset Pair Compare

Use this when you want repeatable preset-to-preset execution.

1. In `Preset Pair Compare`, set `baseline_preset`.
2. Set `target_preset`.
3. Optionally use:
   - `Low -> Current`
   - `Low -> Sionna`
   - `Low -> PO-SBR`
4. Click `Run Preset Pair Compare`.
5. Read:
   - selected pair forecast
   - compare runner status
   - compare assessment in `Artifact Inspector`

### Sequence 4: Export A Decision Package

Use this when the operator decision is ready to hand off.

1. Ensure the compare pair is final.
2. Click `Policy Gate`.
3. Click `Run Session`.
4. Click `Export Gate`.
5. Click `Export Session`.
6. Click `Export Brief`.

## What Confirms Backend Connection

The strongest practical signs are:

1. `Run Graph (API)` returns a valid `graph_run_id`.
2. `Runtime Diagnostics` changes from planned state to observed state.
3. `Decision Pane` compare buttons affect real runs, not only UI state.
4. `Artifact Inspector` shows current and compare artifact evidence.
5. The latest browser E2E report is green:
   - [graph_lab_playwright_e2e_latest.json](reports/graph_lab_playwright_e2e_latest.json)

## Common Problems

### `Run Graph (API)` does not produce a run

Check in this order:

1. backend health on `:8101`
2. `Validate Graph Contract`
3. runtime provider and module fields
4. `Runtime Diagnostics`

### Compare runner is blocked

Usually this means:

- the required runtime module is missing
- the selected runtime needs a license or repo path
- the target preset is incomplete

### Paid RadarSimPy path does not behave like production

Check:

- `License Tier = production`
- `License File` points to the real `.lic`
- the paid evidence set in [Generated Reports Index](reports/README.md)

## Related Documents

- [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md)
- [Graph Lab Button Scenario Guide](302_graph_lab_button_scenario_guide.md)
- [Graph Lab 버튼 시나리오 가이드](303_graph_lab_button_scenario_guide_ko.md)
- [Project Structure And User Manual](282_project_structure_and_user_manual.md)
- [Documentation Index](README.md)
- [Generated Reports Index](reports/README.md)
