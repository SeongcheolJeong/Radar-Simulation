# Graph Lab Failure Reading Guide

## Purpose

Use this guide when Graph Lab is open, but a run, compare, gate, or export flow failed or looks blocked.

Use it after:

- `Run Graph (API)`
- `Retry Last Run`
- `Run Low -> Current Compare`
- `Run Preset Pair Compare`
- `Policy Gate`
- `Run Session`
- `Export Brief`

If you need the full screen walkthrough, use [Graph Lab UX Manual](300_graph_lab_ux_manual.md).

If you need the shortest click path first, use [Graph Lab Live Checklist](306_graph_lab_live_checklist.md).

## Screen Reference

Annotated full layout:

![Graph Lab annotated](reports/graph_lab_playwright_snapshots/latest/page_full_annotated.png)

Decision area:

![Decision Pane annotated](reports/graph_lab_playwright_snapshots/latest/decision_pane_annotated.png)

Artifact area:

![Artifact Inspector annotated](reports/graph_lab_playwright_snapshots/latest/artifact_inspector_annotated.png)

Run failed example:

![Graph Lab run failed example](reports/graph_lab_playwright_snapshots/latest/graph_lab_run_failed_example.png)

## Read Failures In This Order

1. top status bar
2. `Graph Run Result`
3. `Runtime Diagnostics`
4. `Decision Pane`
5. `Artifact Inspector`

Do not start from missing artifacts. Start from the run state and runtime diagnostics.

## Failure Case 1: `Run Graph (API)` Failed

Read:

1. top status bar
2. `Graph Run Result`
3. `Runtime Diagnostics`
4. then the runtime preset/backend/license fields in the left panel

Usually means:

- required runtime modules are unavailable
- license tier or `.lic` path is wrong
- provider-specific runtime input is incomplete
- graph contract was not valid enough for the selected backend

Fastest next action:

- rerun `Validate Graph Contract`
- re-read the runtime preset/backend/provider/license fields
- use `Retry Last Run` only if the configuration itself is still correct

## Failure Case 2: Compare Flow Is Blocked Or Empty

Read:

1. `Decision Pane`
2. `Track Compare Workflow`
3. `Preset Pair Compare`
4. `Graph Run Result`
5. `Artifact Inspector`

Usually means:

- no valid compare reference was loaded
- baseline run did not complete
- low-fidelity baseline could not be built
- compare state is stale relative to the current run

Fastest next action:

- use `Use Current as Compare` after a completed run
- or rerun `Run Low -> Current Compare`
- confirm current and compare artifacts both exist

## Failure Case 3: `Policy Gate` Does Not Produce A Usable Decision

Read:

1. `Decision Pane`
2. compare assessment summary
3. selected pair forecast
4. `Artifact Inspector`

Usually means:

- compare evidence is incomplete
- current-vs-compare pair is not the pair you think it is
- the pair was built, but no meaningful compare evidence was loaded

Fastest next action:

- confirm the selected compare pair first
- rerun the pair if needed
- only then rerun `Policy Gate`

## Failure Case 4: Export Or Session Flow Is Empty

Read:

1. `Decision Pane`
2. session/export area
3. `Graph Run Result`
4. `Artifact Inspector`

Usually means:

- no valid run pair existed before session/export
- gate/session/export was attempted before compare evidence existed
- compare history selection is stale

Fastest next action:

- rebuild a valid current-vs-compare pair
- rerun `Policy Gate`
- then rerun `Run Session` or `Export Brief`

## Failure Case 5: The Run Is Green But The Evidence Looks Wrong

Read:

1. `Runtime Diagnostics`
2. `Artifact Inspector`
3. `Decision Pane`

Usually means:

- backend/provider state differs from what you intended
- current artifact and compare artifact are from different contexts
- runtime path changed between baseline and target

Fastest next action:

- compare planned vs observed runtime diagnostics
- inspect current/compare artifact rows in the inspector
- rebuild the pair if the runtime path changed unexpectedly

## Fast Decision Table

| If this failed | Read first | Usually wrong | Next action |
| --- | --- | --- | --- |
| `Run Graph (API)` | `Graph Run Result` | runtime/license/provider/backend issue | validate contract and rerun |
| low-vs-high compare | `Decision Pane` | missing compare reference or blocked low path | rebuild compare pair |
| `Policy Gate` | compare assessment | incomplete or wrong pair | rerun compare then gate |
| `Run Session` / `Export Brief` | session/export area | no valid compare evidence yet | build pair, gate, then export |
| green run but strange evidence | `Runtime Diagnostics` | wrong backend/provider/runtime source | align runtime and rerun |

## Related Documents

- [Graph Lab UX Manual](300_graph_lab_ux_manual.md)
- [Graph Lab Button Scenario Guide](302_graph_lab_button_scenario_guide.md)
- [Artifact Inspector Quick Guide](304_artifact_inspector_quick_guide.md)
- [Graph Lab Live Checklist](306_graph_lab_live_checklist.md)
- [Graph Lab Document Map](322_graph_lab_doc_map.md)
