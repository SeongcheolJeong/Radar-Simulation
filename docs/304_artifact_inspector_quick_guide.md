# Artifact Inspector Quick Guide

## Purpose

Use this guide when:

- you ran `Run Graph (API)` and want to know where to look next
- the right panel shows many lines and you only want the practical reading order
- you want to know whether the current run looks healthy before exporting a brief

For the full frontend walkthrough, use [Graph Lab UX Manual](300_graph_lab_ux_manual.md).

## Where It Is

The `Artifact Inspector` is in the right panel, below `Graph Run Result`.

If you do not see it:

1. run `Load #1`
2. run `Run Graph (API)`
3. scroll down in the right panel

Example:

![Artifact Inspector](reports/graph_lab_playwright_snapshots/latest/artifact_inspector.png)

Annotated example:

![Artifact Inspector annotated](reports/graph_lab_playwright_snapshots/latest/artifact_inspector_annotated.png)

## Read Order

Read the panel in this order:

1. current artifact presence
2. compare evidence, if a compare run is loaded
3. `artifacts:`
4. `node trace:`
5. `visuals:`
6. inspector state lines such as audit and maintenance

This order prevents mixing run status with maintenance metadata too early.

## What Each Area Means

### 1. Current Artifact Presence

This tells you whether the current run actually produced the expected outputs.

Healthy:

- current artifact rows are present
- expected files are listed

Usually unhealthy because:

- the run failed before writing outputs
- the backend path changed and produced fewer artifacts than expected

### 2. Compare Evidence

This appears after a compare run is loaded or created.

Use it to answer:

- is current different from compare
- are shapes still aligned
- did path count or peak bins drift
- is the current pair acceptable for gate/session/export

Healthy:

- compare evidence is present when you expected a compare run
- compare assessment is understandable and not unexpectedly degraded

### 3. `artifacts:`

This is the fastest practical file check.

Look for:

- `path_list.json`
- `adc_cube.npz`
- `radar_map.npz`
- `graph_run_summary.json`
- optional `lgit_customized_output.npz`

Use this section when you want to confirm that the run created real files, not just a status line.

### 4. `node trace:`

This shows which graph nodes participated in the run.

Use it when:

- the graph looks valid but the backend result is surprising
- you want to confirm the flow from source to map

### 5. `visuals:`

This gives visual output references for quick recognition.

Use it when:

- you want a fast human check before opening files directly
- you need a screenshot-oriented review instead of raw artifact paths

### 6. Inspector State

This includes:

- layout state
- probe state
- audit state
- maintenance state

These lines do not tell you whether the simulation itself is correct. They tell you whether the panel state is fresh, customized, truncated, or carrying maintenance provenance.

## Healthy Fast Check

After a normal successful run, a good quick read is:

1. `Graph Run Result` says `status: completed`
2. `Artifact Inspector` shows current artifact rows
3. `artifacts:` includes the expected files
4. if compare is loaded, compare evidence also appears

If all four are true, the frontend/backend path is usually healthy enough for the next step.

## Common Scenarios

### Scenario A: Simple Successful Run

1. `Load #1`
2. `Low Fidelity: RadarSimPy + FFD`
3. `Run Graph (API)`
4. read:
   - `Graph Run Result`
   - current artifact presence
   - `artifacts:`

Expected result:

- `status: completed`
- artifact files are listed

### Scenario B: Compare Current vs High Fidelity

1. run low fidelity
2. `Use Current as Compare`
3. switch to `High Fidelity: PO-SBR` or `High Fidelity: Sionna-style RT`
4. `Run Graph (API)` again
5. read:
   - compare evidence
   - compare assessment
   - artifact deltas

Expected result:

- current and compare evidence both exist
- drift, shape, and artifact differences are visible

### Scenario C: Run Failed

If the run failed, do not start from `Artifact Inspector`.

Read in this order:

1. top status bar
2. `Graph Run Result`
3. `Runtime Diagnostics`
4. only then inspect whether current artifacts are missing

Reason:

- failed runs often produce partial or no artifacts
- the root cause is usually clearer in `Graph Run Result` than in artifact absence

For the button flow, use [Graph Lab Button Scenario Guide](302_graph_lab_button_scenario_guide.md).

## Local Buttons In Artifact Inspector

| Button | Use it when | Result |
| --- | --- | --- |
| `Collapse Inspector Evidence` | the panel is too noisy | hides detail sections |
| `Expand Inspector Evidence` | detail is needed again | reopens detail sections |
| `Reset Inspector Layout` | fold/layout state became confusing | restores default layout |
| `Apply Recommended Audit Action` | audit trail is truncated and the panel recommends cleanup | clears the recommended audit overflow state |
| `Clear Action Trail` | you want to remove retained inspector action history | clears audit history only |
| `Clear Maintenance Marker` | maintenance provenance has already been reviewed | clears the current maintenance marker |
| `Clear Last Clear Record` | old clear-provenance should no longer be retained | clears the stored last-clear record |

## What Not To Overread

Do not overread these as simulation failures by themselves:

- `layout:customized`
- `probe:customized`
- `maintenance:marked`
- `maintenance_clear:recorded`

These are operator-panel state markers, not direct simulation errors.

## Practical Decision Rule

Use this rule:

- if `Graph Run Result` is red, debug the run first
- if `Graph Run Result` is green but artifacts are missing, inspect the backend path
- if artifacts exist and compare evidence looks reasonable, move to `Policy Gate` or `Export Brief`

## Related Documents

- [Graph Lab UX Manual](300_graph_lab_ux_manual.md)
- [Graph Lab Button Scenario Guide](302_graph_lab_button_scenario_guide.md)
- [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md)
- [Generated Reports Index](reports/README.md)
