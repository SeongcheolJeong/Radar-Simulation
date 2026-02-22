# ReactFlow Simulink-Style Web E2E Expansion Plan (M16)

## Objective

Evolve the current AVX-like dashboard into a **block-graph radar development workspace** (Simulink-style UX) while reusing existing backend physics/orchestration assets.

Primary goal:

- enable radar developers to design, run, inspect, compare, and gate full pipelines from scene inputs to adoption decisions in one web workflow

## Why This Direction

- current backend stack already supports core physics and run/gate/report flow
- current frontend confirms workflow value but is monolithic and form-driven
- ReactFlow provides graph editing/traceability UX that matches real radar development tasks

## User-Critical Requirements (Must Reflect in Scope)

### 1) Algorithm developer

- needs: rapid parameter iteration, node-level rerun, RD/RA impact visibility
- required capability:
  - graph parameter editing with immediate validation
  - partial rerun from changed node (not full rerun always)
  - node output quicklook (Path/ADC/RD/RA)

### 2) RF/antenna developer

- needs: `.ffd` effect inspection without full pipeline ambiguity
- required capability:
  - antenna node with `.ffd` attachment and metadata preview
  - before/after compare on selected node outputs

### 3) Physics/runtime developer

- needs: fast/balanced/fidelity mode switching for same graph
- required capability:
  - profile toggle attached to run request
  - backend/runtime resolution shown per node

### 4) Validation/release owner

- needs: deterministic gate evidence and reproducible handoff
- required capability:
  - graph-run to regression-session mapping
  - policy verdict + top failure evidence + report export in one loop

### 5) Team lead/program manager

- needs: quick health/risk visibility for multiple runs
- required capability:
  - compact overview with run status, gate badge, trend, blockers

## Product Surface (v1)

1. Graph Editor
2. Property Inspector
3. Run Monitor (per-node state/log)
4. Artifact Inspector (Path/ADC/RD/RA)
5. Compare + Policy Gate
6. Evidence Drill-Down + Decision Report Export
7. Template Library (starter graphs)

## Architecture Overview

### Frontend

- framework: React + `@xyflow/react`
- layout:
  - left: node palette/templates
  - center: graph canvas
  - right: node properties + execution output tabs
  - bottom: run timeline/log

### Backend

- keep existing endpoints operational
- add graph endpoints:
  - `POST /api/graph/validate`
  - `POST /api/graph/runs`
  - `GET /api/graph/runs/{run_id}`
  - `GET /api/graph/runs/{run_id}/nodes/{node_id}`
  - `POST /api/graph/runs/{run_id}/cancel`

### Node Execution Mapping (initial)

- `SceneSource` -> scene json input
- `RadarConfig` -> radar/profile parameters
- `Propagation` -> analytic/sionna/po_sbr route
- `AntennaPattern` -> `.ffd` interpolation attachment
- `SynthFMCW` -> ADC generation
- `RadarMap` -> RD/RA generation
- `ComparePolicy` -> parity/policy eval
- `RegressionGate` -> session/export package
- `ReportExport` -> markdown handoff

## Data Contracts (Freeze First)

### Graph spec (`graph_schema_v1`)

- graph metadata (`graph_id`, `version`, `created_at`)
- nodes (`id`, `type`, `params`, `ui`)
- edges (`id`, `source`, `target`, `contract`)
- run profile (`fast_debug|balanced_dev|fidelity_eval`)

### Node artifact envelope

- `artifact_type`, `path`, `summary`, `created_at`, `producer_node_id`

### Determinism and replay

- each graph run stores:
  - input graph snapshot
  - resolved runtime config
  - node execution sequence
  - artifact index and checksums (where available)

## Delivery Milestones (M16)

### M16.0 Contract Freeze

- deliverables:
  - graph schema md + examples
  - validator request/response contract
- exit criteria:
  - 5 sample graphs validate/pass with reproducible errors on invalid graphs

### M16.1 ReactFlow Shell

- deliverables:
  - React app scaffold
  - basic graph CRUD + template load
  - inspector skeleton
- exit criteria:
  - open/edit/save/load graph in browser

### M16.2 Graph Executor Bridge

- deliverables:
  - backend graph run API
  - node registry using existing pipeline functions
- exit criteria:
  - one full graph run produces artifact index and run summary

### M16.3 Artifact Inspector

- deliverables:
  - node output viewers (Path/ADC/RD/RA)
  - output trace links to files
- exit criteria:
  - selected node output visible without leaving graph UI

### M16.4 Gate + Evidence Integration

- deliverables:
  - compare/policy/regression integration on graph runs
  - evidence drill-down and decision report from graph context
- exit criteria:
  - adopt/hold decision can be made and exported from graph UI

### M16.5 Hardening

- deliverables:
  - partial rerun cache
  - cancel/retry handling
  - failure surfacing and recovery guidance
- exit criteria:
  - stable under repeated run/edit loops

## Efficiency Rules (Avoid Waste)

1. freeze contracts first, then UI/engine changes
2. keep node catalog minimal in v1 (no broad node explosion)
3. avoid simultaneous large physics + frontend rewrites
4. each milestone must end with:
   - contract doc
   - validation command
   - validation log entry
5. if a milestone fails twice without new signal, re-plan before continuing

## Risks and Mitigation

- risk: monolithic frontend migration overhead
  - mitigation: run new ReactFlow app in parallel path, keep existing dashboard usable
- risk: runtime-specific backend divergence
  - mitigation: node executor contracts hide backend details behind normalized output schema
- risk: review complexity for non-experts
  - mitigation: provide template graphs + guided default presets + clear failure messages

## Immediate Next Action

- implement M16.0 graph contract docs and validator stub while keeping current dashboard operational.
