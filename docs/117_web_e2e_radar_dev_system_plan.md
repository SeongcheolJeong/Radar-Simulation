# Web-Based E2E Radar Development System Plan

## Goal

Build a web-based developer system for autonomous-driving radar R&D that supports:

1. Scene-to-signal full chain (`scene -> path_list -> raw_adc -> RD/RA -> detection/tracking`)
2. Fast iteration for algorithm engineers and physics engineers
3. Reproducible E2E quality/performance comparison across configurations

## Current Readiness (Starting Point)

- Core backend contracts are in place (`path_list`, `adc_cube`, `radar_map`)
- Multi-backend scene pipeline exists (`analytic_targets`, `hybrid_frames`, `sionna_rt`, `po_sbr_rt`)
- Frontend starter viewer exists (`frontend/avx_like_dashboard.html`)
- Major open gap: strict PO-SBR runtime evidence on Linux+NVIDIA

Conclusion: expansion to full web E2E system can start now.

## 1) Interface Inventory (What radar developers need)

| Page | Primary user | Must-view panels | Main inputs | Main outputs |
|---|---|---|---|---|
| Workspace Home | Team lead, all devs | Project health, latest runs, pass/fail trend, runtime readiness | Project selection, branch/profile | Run queue status, regression trend cards |
| Scenario Studio | Simulation engineer | 2D/3D scene, ego trajectory, target list, material assignment | Scene JSON, glTF/OBJ/sidecar, scenario preset | Versioned scene package |
| Radar & Waveform Designer | Radar algorithm engineer | RF/waveform editor, TX/RX geometry, TDM schedule editor, derived metrics | `fc`, `B`, `Tchirp`, `fs`, chirps/frame, Tx/Rx config | Versioned radar config + validation report |
| Antenna/FFD Studio | RF/antenna engineer | FFD preview, gain/polarization cuts, element map | `.ffd`, interpolation options, Jones settings | Pattern cache + calibration profile |
| Physics Model Studio | Physics engineer | Path statistics, reflection-order histogram, material contribution chart | Backend choice, reflection/diffuse/clutter toggles | Path model config + physics summary |
| Run Orchestrator | All devs | Job form, run graph, cost/runtime estimate, worker assignment | Scenario + radar + backend + profile | Run record, artifact links |
| Signal Chain Explorer | Algorithm engineer | Raw ADC slice, range FFT, Doppler FFT, RA map, phase diagnostics | Chirp/rx/tx index, window/FFT settings | Debug snapshots, export tables |
| Detection & Tracking | Perception engineer | Detection list, track timeline, gating/association diagnostics | CFAR/threshold/cluster/tracker params | Detections/tracks JSON, KPI report |
| Compare & Regression | QA, lead | A/B diff dashboard, metric deltas, drift heatmaps | Baseline run vs candidate run | Regression decision report |
| Performance & Cost | Infra/perf engineer | Runtime breakdown, memory, GPU utilization, throughput | Speed/accuracy mode, worker pool | Cost/perf report |
| Artifact & API Browser | All devs | Contract schemas, artifact manifest, provenance trace | run_id, artifact type | Download bundle + reproducibility manifest |

## 2) Inputs developers should control

### Scenario inputs

- Scene geometry: object list, glTF/OBJ import, material map
- Ego motion: position/velocity/yaw timeline
- Dynamic targets: range/velocity/trajectory templates
- Weather/noise placeholders (for later extension)

### Radar inputs

- Hardware: Tx/Rx count, antenna positions, spacing
- Waveform: `fc`, slope, bandwidth, chirp duration, sampling rate
- TDM-MIMO schedule: TX firing order and chirp mapping

### DSP/algorithm inputs

- FFT sizes, windows, range-bin limit
- Motion compensation toggles
- CFAR and clustering thresholds
- Tracker parameters (init, gating, confirmation/deletion)

### Physics inputs

- Backend selection: `analytic_targets | hybrid_frames | sionna_rt | po_sbr_rt`
- Reflection order limit, diffuse/clutter enable flags
- Polarization/Jones enable flag
- Material weighting and path-power fit selection

### Calibration/validation inputs

- `.ffd` file sets and interpolation options
- Scenario profile lock policy
- Measured replay pack selection

## 3) Views developers should have (including beyond your list)

### Must-have visualization set

- Top-down scene with FOV cone and target overlays
- Path-level debug view (per chirp, per path id, material-tag color)
- Raw ADC viewer (TX/RX/chirp slicing)
- RD map and RA map synchronized cursor view
- Detection/track table linked to map points

### Strongly recommended extra views

- Path provenance panel: which backend/model produced each path
- Error budget panel: physics/model/DSP contribution estimate to total error
- Timeline scrubber: chirp/frame temporal consistency check
- Reproducibility diff view: config hash/env hash change detector
- Failure triage panel: run failed at which stage and why

## 4) Outputs beyond viewing (must be exportable)

1. `path_list.json` (expanded schema: path_id/material/reflection_order/pol)
2. `adc_cube.npz` (canonical 4D)
3. `radar_map.npz` (RD/RA + metadata)
4. `detections.json`, `tracks.json` (new)
5. `run_summary.json` (all config fingerprints + KPIs)
6. `parity_report.json` / `regression_report.json`
7. `run_bundle.zip` (scene + config + artifacts + environment snapshot)

## 5) Speed vs Accuracy profile system (critical)

| Profile | Goal | Backend priority | Typical settings | Use case |
|---|---|---|---|---|
| `fast_debug` | shortest iteration | `analytic_targets` or lightweight `sionna_rt` | low chirp/sample, reduced FFT, limited reflections, no polarization | UI/algorithm logic debug |
| `balanced_dev` | daily development default | `sionna_rt` | medium chirp/sample/FFT, motion compensation on, selective physics | model tuning and feature dev |
| `fidelity_eval` | quality gate | `sionna_rt full` or `po_sbr_rt` (when ready) | high resolution, richer multipath/polarization, strict lock policy | release candidate evaluation |

Profile must be first-class (saved, shareable, diffable), not just a temporary UI toggle.

## 6) System architecture for web E2E

### Backend services

- `orchestrator-api` (FastAPI): run create/query/cancel, compare, export
- `worker-runner`: executes existing scripts/pipeline with job manifest
- `artifact-index`: stores run metadata and searchable KPI summaries
- `event-stream`: WebSocket/SSE for real-time run progress

### Data model (minimum)

- `scenario_version`
- `radar_config_version`
- `physics_profile_version`
- `run_id` / `parent_run_id`
- `artifact_manifest`
- `metric_snapshot`
- `environment_fingerprint`

### Frontend structure

- `AppShell` + page routing
- `RunWizard` (scenario/config/profile selection)
- `ResultExplorer` (scene/signal/detection tabs)
- `CompareView` (A/B and regression)
- `ProfileManager` (speed/accuracy presets)

## 7) Phased implementation plan

## Phase 0: Contract freeze and API skeleton

- Freeze JSON contracts for scenario, run request, run summary
- Wrap current script entrypoints behind internal Python service layer
- Deliverables:
  - `/api/runs` basic create/get/list
  - deterministic `run_summary.json` schema v1

Acceptance:

- one run can be triggered from API and returns existing 3 artifacts

## Phase 1: Web MVP (developer usable)

- Implement pages: Home, Run Orchestrator, Result Explorer(min)
- Load existing demo and new run outputs in web UI
- Deliverables:
  - run submission form
  - progress streaming
  - RD/RA + detection list + top-down scene

Acceptance:

- user can run one scene from web and inspect outputs end-to-end

## Phase 2: Design pages and advanced controls

- Add Scenario Studio, Radar/Waveform Designer, Antenna/FFD Studio
- Add save/load versioned config sets
- Deliverables:
  - config diff viewer
  - `.ffd`-aware parameter workflow

Acceptance:

- no manual JSON editing needed for standard workflows

## Phase 3: Compare/Regression and quality gates

- Implement A/B compare page and drift reports
- Integrate pass/fail policy controls
- Deliverables:
  - baseline pinning
  - automatic regression report generation

Acceptance:

- one-click compare between two runs with policy verdict

## Phase 4: Calibration/measured replay integration

- Integrate measured pack and replay plans in web flow
- Add scenario profile lock management UI
- Deliverables:
  - calibration workflow dashboard
  - profile lock lifecycle panel

Acceptance:

- measured replay path can be configured and executed from web

## Phase 5: Performance/cost optimization and infra scale

- Add queue prioritization, worker tags (CPU/GPU), artifact retention policy
- Add runtime profiling and cost dashboards

Acceptance:

- team can track throughput and choose profile by cost/quality target

## Phase 6: PO-SBR production readiness

- Close M14.6 strict evidence on Linux+NVIDIA
- Expose PO-SBR profile in UI as selectable fidelity option

Acceptance:

- `fidelity_eval` profile includes validated PO-SBR runtime path

## 8) Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| PO-SBR runtime platform dependency | blocks highest-fidelity mode | keep `fidelity_eval` split into `sionna_fidelity` and `po_sbr_fidelity` until M14.6 closes |
| Artifact size explosion (`adc_cube`) | storage and UI lag | NPZ chunking/Zarr option + downsample preview artifacts |
| UI overload from too many controls | poor usability | profile presets + advanced mode folding + role-based defaults |
| Non-reproducible runs | regression trust loss | strict run manifest + environment hash + immutable artifact index |

## 9) Immediate next actions (recommended)

1. Define web API contract draft (`run_request`, `run_summary`, `compare_request`) and freeze v1.
2. Implement `Phase 0` service wrapper over existing scripts (no physics rewrite).
3. Extend current dashboard to call API instead of static JSON-only mode.
4. Add profile manager (`fast_debug`, `balanced_dev`, `fidelity_eval`) as first-class object.
5. Start parallel Linux PO-SBR closure track for Phase 6 readiness.

## 10) Decision for your question

- You can proceed now with web E2E expansion.
- Backend and physics are usable for development-grade system build.
- For production-grade high-fidelity physics claim, PO-SBR Linux strict completion is still required.
