# Frontend Radar Developer Workbench Plan (2026-03-03)

Reference:
- `docs/Frontendref.md`

## Goal
Turn current Graph Lab + Dashboard into a Radar developer-first workbench where design, runtime execution, parity/gate decision, and report export happen in one UI loop.

## Product Principles
1. One-loop workflow: `Design -> Run -> Inspect -> Gate -> Export`.
2. Runtime transparency: backend/runtime/license state must be visible at all times.
3. Deterministic engineering UX: cache, rerun, and failure evidence must be explicit.
4. Keep current static frontend path operational while incrementally improving architecture.

## Execution Plan

### Phase 1 (Now): Runtime/Licensing Visibility + Run Payload Alignment
- [x] Add runtime/license HUD in top bar.
- [x] Add runtime configuration controls in Graph Inputs panel.
- [x] Pass runtime configuration from frontend to graph run request.
- [x] Add graph-run `scene_overrides` support in backend.
- [x] Apply per-run scene overrides into effective scene JSON for execution.
- [x] Include override application status in graph run summary execution block.
- [x] Add RadarSimPy runtime provider support for `runtime_input.license_file` override.

### Phase 2: Artifact Inspector v2
- [x] Add RD/RA cursor probe and peak lock tooling.
- [x] Add run-to-run diff overlay in inspector.
- [x] Add cache-hit vs recomputed artifact badge per node output.

### Phase 3: Decision Surface Unification
- [x] Merge compare/policy/session/export controls into one decision pane.
- [x] Auto-summarize top failure evidence lines for release owner.
- [x] Add one-click decision markdown export with artifact links.

### Phase 4: Frontend Hardening
- [x] Split large panel module into focused modules (`runtime`, `artifact`, `gate`, `audit`).
- [x] Add Playwright browser E2E for graph run/gate/export critical paths.
- [x] Add visual regression snapshots for key panels.

### Phase 5: Developer Workbench UX Layer
- [x] Add top-level pipeline rail (`Design -> Run -> Inspect -> Gate -> Export`) driven by live run state.
- [x] Add layout mode switch (`triad`, `build`, `review`, `focus`) for different developer workflows.
- [x] Add density mode switch (`comfortable`, `compact`) for high-information sessions.
- [x] Add focus-mode drawer controls for inputs/inspector with backdrop close behavior.
- [x] Add responsive behavior that keeps Graph Lab operational on desktop and mobile widths.
- [x] Stabilize Playwright strict snapshots with deterministic normalization + stable-target compare set.

## Done in This Iteration
1. Runtime/Licensing HUD and controls are implemented in Graph Lab UI.
2. Frontend graph run payload now carries runtime scene overrides.
3. Backend applies scene overrides and records effective scene path/override status.
4. RadarSimPy runtime provider now accepts runtime license file from request-level runtime input.
5. Artifact Inspector now supports RD/RA cursor probing with peak lock against top-peak bins.
6. Artifact Inspector now shows run-to-run diff overlay (shape/peak/path deltas) with auto baseline loading.
7. Node trace now distinguishes cache-hit vs recomputed artifacts per node output.
8. Decision Pane now unifies compare/pin/gate/regression/export actions in Node Inspector.
9. Decision Pane auto-generates release-owner summary evidence lines from gate/diff metadata.
10. One-click Decision Brief markdown export now includes artifact links and regression references.
11. Panel responsibilities are split into focused modules (`panels/runtime.mjs`, `panels/artifact.mjs`, `panels/gate.mjs`, `panels/audit.mjs`).
12. New Playwright browser E2E validator covers run/pin/gate/session/export critical path.
13. Visual snapshot baseline/latest workflow is added under `docs/reports/graph_lab_playwright_snapshots/`.
14. Top bar now includes pipeline stage rail with live completion state.
15. Workbench view modes (`triad/build/review/focus`) and density modes (`comfortable/compact`) are implemented.
16. Focus-mode now provides drawer toggles for Graph Inputs/Node Inspector and supports quick close from backdrop/ESC.
17. HTML/CSS shell now supports responsive topbar/workbench layout for both desktop and narrow screens.
18. Playwright strict E2E now runs with required runtime and deterministic snapshot matching (`topbar`, `decision_pane`, `artifact_inspector`).
19. CI workflow now enforces Graph Lab Playwright strict visual gate and uploads latest snapshot artifacts.

## Validation Command
- `PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py`
- `PYTHONPATH=src .venv/bin/python scripts/validate_graph_lab_playwright_e2e.py --require-playwright --strict-visual --output-json docs/reports/graph_lab_playwright_e2e_latest.json`
- `node --check frontend/graph_lab/app.mjs`
- `node --check frontend/graph_lab/panels.mjs`
