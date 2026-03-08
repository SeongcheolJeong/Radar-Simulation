# Install Onboarding Map

## Purpose

Use this page when you do not yet know which installation path you need.

This is the one-page decision map for:

- base usage
- RadarSimPy low-fidelity usage
- Sionna-style RT usage
- PO-SBR usage

## Quick Decision

| Your goal | Start here | Runtime env |
| --- | --- | --- |
| I want to open the frontend and run the basic demo | [Base Environment](284_install_base_environment.md) | `.venv` |
| I want the low-fidelity `RadarSimPy + FFD` track | [RadarSimPy Runtime](285_install_radarsimpy_runtime.md) | usually `.venv` |
| I want the high-fidelity `Sionna-style RT` track | [Sionna-Style RT Runtime](286_install_sionna_style_rt_runtime.md) | `.venv-sionna311` |
| I want the high-fidelity `PO-SBR` track on Linux + NVIDIA | [PO-SBR Runtime](287_install_po_sbr_runtime.md) | `.venv-po-sbr` |
| I only want to validate backend/API behavior | [Base Environment](284_install_base_environment.md) | `.venv` |
| I want paid RadarSimPy production gates | [RadarSimPy Runtime](285_install_radarsimpy_runtime.md) | `.venv` + paid `.lic` |

## Recommended Order

1. Install the base environment first.
2. Confirm the backend/API validator passes.
3. Run Graph Lab locally.
4. Add only the runtime-specific environment you actually need.

Base entry:

- [Base Environment](284_install_base_environment.md)

## Decision Flow

```text
Need only demo / frontend / API?
  -> Base Environment

Need low-fidelity reference track?
  -> RadarSimPy Runtime

Need higher-fidelity RT path on Mitsuba/Dr.Jit?
  -> Sionna-Style RT Runtime

Need Linux + NVIDIA + PO-SBR?
  -> PO-SBR Runtime
```

## Environment Strategy

Recommended split:

- `.venv`
  - base environment
  - backend API
  - classic dashboard
  - Graph Lab general use
  - RadarSimPy if your setup fits the base env
- `.venv-sionna311`
  - Sionna / Mitsuba / Dr.Jit runtime work
- `.venv-po-sbr`
  - Linux GPU PO-SBR work

Why this split is better:

- runtime dependencies are optional and heavy
- not every user needs every backend
- separating environments reduces cross-backend breakage

## First Successful Path

If you are new to this repository, do this first:

1. [Base Environment](284_install_base_environment.md)
2. run:

```bash
cd /path/to/myproject
PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py
```

3. then run:

```bash
cd /path/to/myproject
PY_BIN=.venv/bin/python scripts/run_graph_lab_local.sh 8081 8101
```

4. open:

- `http://127.0.0.1:8081/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8101`

After that, decide whether you need:

- RadarSimPy
- Sionna-style RT
- PO-SBR

## Install Guide Index

- [Base Environment](284_install_base_environment.md)
- [RadarSimPy Runtime](285_install_radarsimpy_runtime.md)
- [Sionna-Style RT Runtime](286_install_sionna_style_rt_runtime.md)
- [PO-SBR Runtime](287_install_po_sbr_runtime.md)

## Related User Docs

- [Project Structure And User Manual](282_project_structure_and_user_manual.md)
- [프로젝트 구조 및 사용자 매뉴얼 (한국어)](283_project_structure_and_user_manual_ko.md)
- [README.md](../README.md)
- [README_ko.md](../README_ko.md)
