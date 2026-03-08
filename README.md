# AVX Radar Simulation Workbench

Language:

- [English](README.md)
- [한국어](README_ko.md)

This repository is a radar simulation workbench for developing and validating FMCW radar pipelines with two practical runtime tracks:

- low fidelity: `RadarSimPy + FFD`
- high fidelity: ray-tracing-backed paths such as `Sionna-style RT` and `PO-SBR`

It includes:

- Python simulation and signal-processing code in `src/avxsim`
- a browser-based operator frontend in `frontend/graph_lab`
- runnable validation and gate scripts in `scripts`
- architecture, workflow, and release documentation in `docs`

Explanation vs evidence:

- explanation: [Documentation Index](docs/README.md)
- evidence: [Generated Reports Index](docs/reports/README.md)

## First 10 Minutes

Do this once first:

1. create the base environment

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy matplotlib
```

2. validate the backend/API path

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py
```

Then choose one track:

### Track A: Graph Lab

Run:

```bash
PY_BIN=.venv/bin/python scripts/run_graph_lab_local.sh 8081 8101
```

Open:

- `http://127.0.0.1:8081/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8101`

Use this when you want:

- runtime selection
- compare workflows
- artifact inspection
- decision brief export

### Track B: Classic Dashboard

Run:

```bash
PY_BIN=.venv/bin/python scripts/run_web_e2e_dashboard_local.sh 8080 8099
```

Open:

- `http://127.0.0.1:8080/frontend/avx_like_dashboard.html?summary=/docs/reports/frontend_quickstart_v1.json&api=http://127.0.0.1:8099`

Use this when you want:

- the simplest demo shell
- a quick API/dashboard smoke path
- a lightweight presentation view

If either track works, continue with:

- [Install Onboarding Map](docs/288_install_onboarding_map.md)
- [Frontend Runtime Purpose Presets](docs/280_frontend_runtime_purpose_presets.md)

## Who Should Use What

| If you are... | Start here | Then use |
| --- | --- | --- |
| new to the repository | [README.md](README.md) | [Install Onboarding Map](docs/288_install_onboarding_map.md) |
| a frontend operator | [README.md](README.md) | `scripts/run_graph_lab_local.sh`, [Frontend Runtime Purpose Presets](docs/280_frontend_runtime_purpose_presets.md) |
| a backend or validation developer | [Project Structure And User Manual](docs/282_project_structure_and_user_manual.md) | `src/avxsim`, `scripts/validate_*`, `scripts/run_*` |
| validating paid RadarSimPy runtime | [RadarSimPy Runtime](docs/285_install_radarsimpy_runtime.md) | `scripts/run_radarsimpy_paid_6m_gate_ci.sh` |
| unsure which runtime to install | [Install Onboarding Map](docs/288_install_onboarding_map.md) | the guide chosen by your goal |

## Frontend Preview

Graph Lab is the main operator UI for runtime selection, compare workflows, artifact inspection, and decision export.

![Graph Lab frontend preview](docs/reports/graph_lab_playwright_snapshots/latest/page_full.png)

Related:

- [Frontend Runtime Purpose Presets](docs/280_frontend_runtime_purpose_presets.md)
- [Project Structure And User Manual](docs/282_project_structure_and_user_manual.md)
- [프로젝트 개요 및 빠른 시작 (한국어)](README_ko.md)

## What File Is Best For User Documentation?

Use both:

1. `README.md`
   - best GitHub landing page
   - short overview, quick install, quick run, docs index
2. `docs/282_project_structure_and_user_manual.md`
   - best place for the full user manual
   - detailed structure, install steps, usage flows, troubleshooting
3. `docs/283_project_structure_and_user_manual_ko.md`
   - Korean detailed manual for user onboarding

This repository now uses that structure.

Documentation hub:

- [Documentation Index](docs/README.md)

## Repository Structure

```text
src/avxsim/     Core simulation, DSP, runtime adapters, API
frontend/       Browser UI: Graph Lab and dashboard shells
scripts/        Launchers, validators, gates, report builders
docs/           Architecture, user guides, contracts, release docs
configs/        Profiles and tuning/config assets
data/           Demo scenes, runtime records, generated artifacts
external/       Optional third-party runtimes and reference repos
tests/          Test data and fixture-oriented test assets
```

Detailed breakdown:

- [Documentation Index](docs/README.md)
- [Project Structure And User Manual](docs/282_project_structure_and_user_manual.md)
- [프로젝트 구조 및 사용자 매뉴얼 (한국어)](docs/283_project_structure_and_user_manual_ko.md)
- [Architecture](docs/03_architecture.md)

## Architecture

The core pipeline is organized around stable interfaces so runtime backends can change without breaking downstream ADC/map consumers.

![Project architecture](docs/architecture.png)

Key modules:

- `PathGenerator`
  - produces `paths_by_chirp`
- `AntennaModel`
  - provides complex TX/RX gains
- `FmcwMultiplexingSynthesizer`
  - converts radar params, paths, and multiplexing plan into ADC cubes
- `OutputWriter`
  - persists `path_list.json`, `adc_cube.npz`, `radar_map.npz`, and optional LGIT output

Dependency rule:

- `PathGenerator -> Synthesizer <- AntennaModel`
- `OutputWriter` depends on contracts, not generator internals

## Installation Guides

- [Install Onboarding Map](docs/288_install_onboarding_map.md)
- [Base Environment](docs/284_install_base_environment.md)
- [RadarSimPy Runtime](docs/285_install_radarsimpy_runtime.md)
- [Sionna-Style RT Runtime](docs/286_install_sionna_style_rt_runtime.md)
- [PO-SBR Runtime](docs/287_install_po_sbr_runtime.md)
- [Documentation Index](docs/README.md)

## Quick Start

### 1. Base Environment

Recommended:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy matplotlib
```

Optional browser E2E validation:

```bash
python -m pip install playwright
python -m playwright install chromium
```

Notes:

- There is no single locked dependency manifest at repo root yet.
- Base demo and API flows work with a lightweight Python environment.
- Runtime backends such as `radarsimpy`, `mitsuba/drjit`, and `rtxpy/igl` are optional and purpose-specific.

### 2. Run The Classic Dashboard Demo

```bash
PY_BIN=.venv/bin/python scripts/run_web_e2e_dashboard_local.sh 8080 8099
```

Open:

- `http://127.0.0.1:8080/frontend/avx_like_dashboard.html?summary=/docs/reports/frontend_quickstart_v1.json&api=http://127.0.0.1:8099`

### 3. Run Graph Lab

```bash
PY_BIN=.venv/bin/python scripts/run_graph_lab_local.sh 8081 8101
```

Open:

- `http://127.0.0.1:8081/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8101`

### 4. Validate The Backend/API Contract

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py
```

### 5. Optional Graph Lab Browser E2E

```bash
PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers \
PYTHONPATH=src .venv/bin/python \
scripts/validate_graph_lab_playwright_e2e.py \
  --require-playwright \
  --output-json docs/reports/graph_lab_playwright_e2e_latest.json
```

## Main User Flows

### Frontend Operator Flow

Graph Lab is the main frontend for interactive operation:

- choose a runtime track in the runtime panel
- run the current graph/session
- compare low fidelity vs high fidelity
- inspect artifacts, diagnostics, and decision brief output

Related docs:

- [Frontend Runtime Purpose Presets](docs/280_frontend_runtime_purpose_presets.md)
- [Frontend Dashboard Usage](docs/116_frontend_dashboard_usage.md)

### Runtime Tracks

- `RadarSimPy + FFD`
  - low-fidelity reference path
  - useful for fast baseline comparison
- `Sionna-style RT`
  - higher-fidelity ray-tracing-oriented path
- `PO-SBR`
  - higher-fidelity physical optics / SBR-oriented path

### Core Artifacts

The main pipeline writes:

- `path_list.json`
- `adc_cube.npz`
- `radar_map.npz`
- optional `lgit_customized_output.npz`

## Detailed Manual

Read the full manual here:

- [Documentation Index](docs/README.md)
- [Project Structure And User Manual](docs/282_project_structure_and_user_manual.md)
- [프로젝트 구조 및 사용자 매뉴얼 (한국어)](docs/283_project_structure_and_user_manual_ko.md)

It covers:

- project structure by directory
- installation paths
- optional runtime backend setup
- frontend usage
- backend validation
- reports and artifacts
- troubleshooting

Generated outputs:

- [Generated Reports Index](docs/reports/README.md)

## Advanced / Production Validation

For paid or production-grade RadarSimPy validation, see:

- `scripts/run_radarsimpy_paid_6m_gate_ci.sh`
- `scripts/run_radarsimpy_production_release_gate.py`
- `scripts/run_radarsimpy_readiness_checkpoint.py`
- `scripts/validate_radarsimpy_simulator_reference_parity_optional.py`

## Current Documentation Recommendation

If your goal is "help a new user install and use this project":

- put the summary in `README.md`
- put the real manual in [`docs/282_project_structure_and_user_manual.md`](docs/282_project_structure_and_user_manual.md)

That is the right structure for GitHub, onboarding, and long-term maintenance.
