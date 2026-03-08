# Project Structure And User Manual

## Purpose

This document is the detailed user manual for this repository.

Use it for:

- understanding the repository structure
- installing a workable local environment
- running the backend and frontend
- choosing the right runtime track
- locating outputs, reports, and troubleshooting information

The root [README.md](../README.md) should stay short and act as the GitHub landing page. This file is the full manual.

Documentation hub:

- [Documentation Index](README.md)

## 1. What This Project Is

This project is an AVX-style radar simulation workbench centered on a stable pipeline:

1. scene or path generation
2. antenna and multiplexing-aware signal synthesis
3. ADC cube generation
4. radar-map and report generation
5. frontend-assisted validation and compare workflows

Current architecture reference:

- [Architecture](03_architecture.md)

Core contract:

- input scene/runtime config
- output artifacts:
  - `path_list.json`
  - `adc_cube.npz`
  - `radar_map.npz`
  - optional `lgit_customized_output.npz`

## 2. Who Should Use Which Entry Point

### New user

Start with:

- [README.md](../README.md)
- this manual

### Frontend operator

Start with:

- `scripts/run_graph_lab_local.sh`
- [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md)

### Backend / validation developer

Start with:

- `src/avxsim`
- `scripts/validate_*`
- `scripts/run_*`

### Paid RadarSimPy validation operator

Start with:

- `scripts/run_radarsimpy_paid_6m_gate_ci.sh`
- `scripts/run_radarsimpy_production_release_gate.py`
- `scripts/run_radarsimpy_readiness_checkpoint.py`

## 3. Repository Structure

### Top Level

```text
README.md
configs/
data/
docs/
external/
frontend/
scripts/
src/
tests/
```

### `src/avxsim`

Main Python package.

Important areas:

- `scene_pipeline.py`
  - high-level scene-to-artifact orchestration
- `runtime_providers/`
  - runtime/backend adapters
  - `radarsimpy_rt_provider.py`
  - `mitsuba_rt_provider.py`
  - `po_sbr_rt_provider.py`
- `synth.py`
  - FMCW/TDM synthesis logic
- `antenna.py`
  - antenna gain handling
- `ffd.py`
  - FFD parsing and interpolation
- `adc_pack_builder.py`
  - ADC / radar-map packaging
- `lgit_output_adapter.py`
  - LGIT-shaped output adapter
- `web_e2e_api.py`
  - backend API used by the frontend

### `frontend`

Browser-side UI.

Main files:

- `frontend/graph_lab_reactflow.html`
  - main operator shell
- `frontend/graph_lab/`
  - Graph Lab modules
- `frontend/avx_like_dashboard.html`
  - simpler dashboard/demo view

### `scripts`

Runnable entry points.

Common categories:

- launchers
  - `run_graph_lab_local.sh`
  - `run_web_e2e_dashboard_local.sh`
- validators
  - `validate_web_e2e_orchestrator_api.py`
  - `validate_graph_lab_playwright_e2e.py`
- backend gates
  - `run_radarsimpy_paid_6m_gate_ci.sh`
  - `run_po_sbr_post_change_gate.py`
- report/build helpers
  - `build_frontend_demo_example.py`
  - `build_release_announcement_pack.py`

### `docs`

Project documentation.

Useful starting points:

- [Architecture](03_architecture.md)
- [Frontend Dashboard Usage](116_frontend_dashboard_usage.md)
- [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md)
- [Compare History Bundle Schema Migration](281_compare_history_bundle_schema_migration.md)

### `data`

Generated and sample artifacts.

Common locations:

- `data/demo/`
  - frontend demo fixtures
- `data/web_e2e/`
  - API-generated run/comparison/session records
- `data/runtime_*`
  - runtime-related sample assets

### `external`

Optional third-party runtimes, mirrors, and references.

Examples:

- `external/radarsimpy*`
- `external/sionna`
- `external/PO-SBR-Python`
- `external/rtxpy-mod`
- `external/HybridDynamicRT`

These are not all required for base usage.

## 4. Installation

Split install guides:

- [Documentation Index](README.md)
- [Install Onboarding Map](288_install_onboarding_map.md)
- [Install Guide: Base Environment](284_install_base_environment.md)
- [Install Guide: RadarSimPy Runtime](285_install_radarsimpy_runtime.md)
- [Install Guide: Sionna-Style RT Runtime](286_install_sionna_style_rt_runtime.md)
- [Install Guide: PO-SBR Runtime](287_install_po_sbr_runtime.md)

### 4.1 Base Installation

Recommended minimum environment for local demo/frontend use:

```bash
cd /path/to/myproject
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy matplotlib
```

Why this is enough for the base path:

- demo generation uses `numpy`
- demo visual output uses `matplotlib`
- Graph Lab itself is static HTML + JS and does not need a Node build

### 4.2 Optional Browser E2E Validation

If you want automated browser checks:

```bash
python -m pip install playwright
python -m playwright install chromium
```

### 4.3 Optional Runtime Backends

This project supports purpose-based runtime choices. Not all are mandatory.

#### RadarSimPy

Needed for:

- `RadarSimPy + FFD`
- paid/trial RadarSimPy runtime checks
- low-fidelity reference track

Relevant files:

- `src/avxsim/radarsimpy_api.py`
- `src/avxsim/runtime_providers/radarsimpy_rt_provider.py`

Notes:

- This repository can work with bundled or locally available RadarSimPy assets when present.
- Paid-license workflows require a valid `.lic` file.

#### Sionna-style RT

Needed modules:

- `mitsuba`
- `drjit`

Used for:

- higher-fidelity RT path generation

#### PO-SBR

Needed modules typically include:

- `rtxpy`
- `igl`

Bootstrap helper:

- `scripts/bootstrap_po_sbr_linux_env.sh`

Used for:

- higher-fidelity PO/SBR path generation

### 4.4 Important Reality

This repository does not currently expose one root-level `requirements.txt` or `pyproject.toml` covering every optional backend combination.

That means:

- base use is straightforward
- full runtime parity use is environment-specific
- optional backends should be installed only when you actually need them

## 5. How To Run

### 5.1 Run The Classic Dashboard Demo

```bash
PY_BIN=.venv/bin/python scripts/run_web_e2e_dashboard_local.sh 8080 8099
```

Open:

- `http://127.0.0.1:8080/frontend/avx_like_dashboard.html?summary=/docs/reports/frontend_quickstart_v1.json&api=http://127.0.0.1:8099`

What this does:

1. builds demo artifacts under `data/demo/frontend_quickstart_v1`
2. starts the backend API
3. starts a static web server

### 5.2 Run Graph Lab

```bash
PY_BIN=.venv/bin/python scripts/run_graph_lab_local.sh 8081 8101
```

Open:

- `http://127.0.0.1:8081/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8101`

What this does:

1. starts the backend API on port `8101`
2. starts a static server on port `8081`
3. serves the Graph Lab UI

### 5.3 Run Backend/API Validation

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py
```

Use this when:

- you changed backend contract behavior
- you want a quick sanity check without opening the browser

### 5.4 Run Graph Lab Browser E2E

```bash
PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers \
PYTHONPATH=src .venv/bin/python \
scripts/validate_graph_lab_playwright_e2e.py \
  --require-playwright \
  --output-json docs/reports/graph_lab_playwright_e2e_latest.json
```

Use this when:

- you changed frontend behavior
- you want to verify real browser flows

## 6. How To Use Graph Lab

Graph Lab is the main operator UI.

## 6.1 Main Idea

You use it to:

- configure a scene/runtime
- run the current configuration
- compare runtime tracks
- inspect artifacts and decision evidence

## 6.2 Purpose Presets

Main presets:

- `Low Fidelity: RadarSimPy + FFD`
- `High Fidelity: Sionna-style RT`
- `High Fidelity: PO-SBR`

Use cases:

- `Low Fidelity`
  - fast reference
  - useful for compare baselines
- `High Fidelity`
  - use when evaluating ray-tracing-backed behavior

Detailed reference:

- [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md)

## 6.3 Recommended Operator Workflow

### Compare low vs high

1. open Graph Lab
2. choose a target high-fidelity preset
3. run current config or use the pair-runner
4. compare against low fidelity
5. inspect `Artifact Inspector`
6. export or review the decision brief

### Fastest route

Use:

- `Run Preset Pair Compare`
- or `Run Low -> Current Compare`

## 6.4 Main Frontend Surfaces

### Runtime Panel

Shows:

- selected backend/provider
- FFD fields
- runtime diagnostics
- provider-specific advanced controls

### Decision Pane

Shows:

- compare workflow state
- compare history
- pinned quick actions
- inspector state mirror
- exported decision summary content

### Artifact Inspector

Shows:

- live compare evidence
- history expectation snapshot
- compare assessment
- audit / maintenance state

## 7. Reports And Outputs

### 7.1 Main Artifacts

Typical output files:

- `path_list.json`
- `adc_cube.npz`
- `radar_map.npz`
- optional `lgit_customized_output.npz`

### 7.2 Generated Reports

Look in:

- `docs/reports/`

Important examples:

- `frontend_quickstart_v1.json`
- `graph_lab_playwright_e2e_latest.json`
- RadarSimPy gate reports
- release pack reports

### 7.3 API Run Records

Look in:

- `data/web_e2e/`

This area stores:

- run records
- comparisons
- regression sessions
- exports

## 8. Paid / Advanced Validation

For production-oriented RadarSimPy validation:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_paid_6m_gate_ci.sh
```

Or run the major components directly:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_production_release_gate.py --license-file /abs/path/license.lic
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_readiness_checkpoint.py --with-real-runtime --runtime-license-tier production --license-file /abs/path/license.lic
PYTHONPATH=src .venv/bin/python scripts/validate_radarsimpy_simulator_reference_parity_optional.py --require-runtime --output-json docs/reports/radarsimpy_simulator_reference_parity_paid_6m.json
```

Use this when:

- validating paid runtime access
- confirming production parity readiness
- generating release-facing reports

## 9. Troubleshooting

### API does not start

Check:

- Python exists in `.venv/bin/python`
- `PYTHONPATH=src` is set for direct Python invocations
- log file under `/tmp/web_e2e_api_<port>.log`

### Frontend loads but actions are blocked

Common cause:

- optional runtime backend is missing

Check:

- runtime diagnostics in Graph Lab
- whether required modules for the chosen preset are installed

### Playwright E2E fails immediately

Check:

- `playwright` Python package installed
- browser installed via `python -m playwright install chromium`

### Dashboard fetch fails in browser

Do not open the HTML with `file://`.

Use:

- `scripts/run_web_e2e_dashboard_local.sh`
- or `scripts/run_graph_lab_local.sh`

so the page is served over `http://`.

### RadarSimPy production gate is blocked

Check:

- `.lic` file path is valid
- paid runtime is actually available
- the expected runtime package or bundled asset exists

## 10. Documentation Strategy Recommendation

If you maintain this repository, keep documentation split like this:

### `README.md`

Use for:

- project overview
- quick install
- quick run
- docs index

### `docs/282_project_structure_and_user_manual.md`

Use for:

- full project structure
- full install manual
- actual user workflow
- troubleshooting

### Specialized docs in `docs/`

Use for:

- architecture contracts
- runtime-provider details
- frontend workflow details
- release and gate reports

This is the right structure for GitHub visibility and long-form user support.
