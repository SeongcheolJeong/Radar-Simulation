# Decision Pane Quick Guide

## Purpose

Use this guide when:

- Graph Lab is already open and you only need the right-side decision workflow
- the `Decision Pane` has too many compare, gate, session, and export controls at once
- you want to know what to read before pressing `Policy Gate` or `Export Brief`

For the full screen walkthrough, use [Graph Lab UX Manual](300_graph_lab_ux_manual.md).

## Where It Is

The `Decision Pane` is in the right panel, above `Artifact Inspector`.

If you do not see it:

1. run `Load #1`
2. run `Run Graph (API)` at least once
3. scroll in the right panel until the compare and gate controls appear

Example:

![Decision Pane](reports/graph_lab_playwright_snapshots/latest/decision_pane.png)

Annotated example:

![Decision Pane annotated](reports/graph_lab_playwright_snapshots/latest/decision_pane_annotated.png)

## Read Order

Read the `Decision Pane` in this order:

1. compare reference state
2. `Track Compare Workflow`
3. `Preset Pair Compare`
4. compare history and quick actions
5. `Policy Gate`
6. session and export actions
7. `Inspector State Mirror`

This order prevents exporting too early or reading inspector state before the current-vs-compare pair is ready.

## What Each Area Means

### 1. Compare Reference State

This tells you whether the current run has a compare partner.

Main signals:

- a compare run is loaded
- current run is pinned as compare
- compare has been cleared

Use this area first when the rest of the pane looks confusing.

### 2. `Track Compare Workflow`

This is the fast operator guide for the current pair.

Use it to answer:

- what is the current track
- what is the compare track
- whether the selected pair is sensible
- what the next action should be

If you only need one summary line before deciding, start here.

### 3. `Preset Pair Compare`

Use this when you want reproducible pair execution instead of manual switching.

Common uses:

- `Low -> Current`
- `Low -> Sionna`
- `Low -> PO-SBR`
- custom `baseline_preset -> target_preset`

Healthy:

- forecast looks reasonable
- pair runner completes without a blocked state

### 4. Compare Session History

This area becomes useful after at least one compare run.

Use it to:

- replay old pairs
- pin important pairs
- rename saved pairs
- inspect retention state
- export or import compare history bundles

Do not start here on a first run.

### 5. `Policy Gate`

Use this only after current and compare evidence both exist.

Healthy:

- current run completed
- compare run completed
- compare assessment is understandable

Usually unhealthy because:

- compare reference is missing
- low path is blocked
- current run failed but the operator tried to gate anyway

### 6. Session And Export

These controls package results for reuse and handoff.

Main actions:

- `Run Session`
- `Export Session`
- `Export Gate`
- `Export Brief`

Use them only after the compare/gate state is already readable.

### 7. `Inspector State Mirror`

This is not the simulation result itself.

It mirrors the current state of `Artifact Inspector` so you can:

- collapse or expand inspector evidence
- reset inspector layout
- apply audit maintenance actions
- read audit and maintenance summaries without scrolling down

## Healthy Fast Check

Before pressing `Policy Gate` or `Export Brief`, check these four things:

1. `Graph Run Result` says `status: completed`
2. compare reference exists when you expect one
3. `Track Compare Workflow` is understandable
4. compare evidence exists in `Artifact Inspector`

If all four are true, the decision path is usually ready.

## Common Scenarios

### Scenario A: Quick Low-vs-Current Compare

1. run low fidelity
2. `Use Current as Compare`
3. switch to the target runtime
4. `Run Graph (API)` again
5. read:
   - compare reference state
   - `Track Compare Workflow`
   - compare assessment
6. only then use `Policy Gate`

### Scenario B: Fastest Automatic Pair

1. configure the target runtime
2. click `Run Low -> Current Compare`
3. read:
   - pair runner result
   - selected pair forecast
   - compare assessment

Expected result:

- low baseline is created automatically
- target run is created automatically
- compare state is filled without manual pinning

### Scenario C: Export Brief For Handoff

1. ensure the pair is readable
2. optional: run `Policy Gate`
3. click `Export Brief`
4. verify that the brief reflects:
   - current vs compare state
   - compare assessment
   - inspector mirror state

If the brief looks wrong, fix the compare state before exporting again.

### Scenario D: Decision Pane Looks Busy

Read only in this order:

1. compare reference state
2. `Track Compare Workflow`
3. `Policy Gate`
4. export buttons

Ignore history and inspector mirror until the main pair is clear.

## Button Group Summary

| Button or area | Use it when | Result |
| --- | --- | --- |
| `Load Compare` | you know an old `graph_run_id` | loads a compare reference |
| `Use Current as Compare` | the current run should become the baseline | pins the current run as compare |
| `Run Preset Pair Compare` | you want a reproducible pair | executes baseline then target |
| `Run Low -> Current Compare` | you want the shortest auto compare | builds low fidelity baseline automatically |
| `Policy Gate` | the pair is ready for a decision | computes the current gate result |
| `Run Session` | you want a session record | writes a regression/decision session |
| `Export Brief` | you need a handoff-ready summary | exports the markdown brief |
| `Inspector State Mirror` controls | inspector state needs adjustment | changes inspector layout/audit state from the decision panel |

## What Not To Overread

Do not treat these as simulation failures by themselves:

- compare history retention metadata
- inspector audit state
- maintenance marker state
- saved or pinned pair metadata

These explain operator workflow state, not raw backend correctness.

## Practical Decision Rule

Use this rule:

- if the run failed, debug `Graph Run Result` first
- if the run passed but compare is missing, fix compare state next
- if compare is readable, run `Policy Gate`
- if gate/export text looks sensible, export the brief

## Related Documents

- [Graph Lab UX Manual](300_graph_lab_ux_manual.md)
- [Graph Lab Button Scenario Guide](302_graph_lab_button_scenario_guide.md)
- [Graph Lab Failure Reading Guide](324_graph_lab_failure_reading_guide.md)
- [Artifact Inspector Quick Guide](304_artifact_inspector_quick_guide.md)
- [Graph Lab Live Checklist](306_graph_lab_live_checklist.md)
