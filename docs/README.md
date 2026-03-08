# Documentation Index

## Purpose

This page is the documentation hub for the `docs/` directory.

Use it when you need to find the right document quickly instead of reading numbered design or contract files in sequence.

For repository summary, start at:

- [English Landing Page](../README.md)
- [Korean Landing Page](../README_ko.md)

For generated evidence and outputs, use:

- [Generated Reports Index](reports/README.md)

## Language Note

- landing pages:
  - [English Landing Page](../README.md)
  - [Korean Landing Page](../README_ko.md)
- detailed manuals:
  - [Project Structure And User Manual](282_project_structure_and_user_manual.md)
  - [프로젝트 구조 및 사용자 매뉴얼](283_project_structure_and_user_manual_ko.md)

Use the landing pages for quick routing. Use `282` and `283` when you want the full user manual in English or Korean.

## Quick Routing

| If you want to... | Read this first | Then use |
| --- | --- | --- |
| understand the repository | [Project Structure And User Manual](282_project_structure_and_user_manual.md) | [Architecture](03_architecture.md) |
| install only what you need | [Install Onboarding Map](288_install_onboarding_map.md) | one of `284` to `287` |
| run Graph Lab | [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md) | `scripts/run_graph_lab_local.sh` |
| run the classic dashboard | [Frontend Dashboard Usage](116_frontend_dashboard_usage.md) | `scripts/run_web_e2e_dashboard_local.sh` |
| validate backend/runtime behavior | [Validation Checkpoints](04_validation_checkpoints.md) | validators and gates in `scripts/` |
| run the fixed release-candidate validation order | [Canonical Validation Scenario Pack](289_canonical_validation_scenario_pack.md) | the scenario commands and evidence files in that pack |
| validate paid RadarSimPy production access | [RadarSimPy Runtime](285_install_radarsimpy_runtime.md) | `scripts/run_radarsimpy_paid_6m_gate_ci.sh` |
| review release-facing evidence | [Generated Reports Index](reports/README.md) | release notes and one-pagers |

## By Role

<a id="role-operator"></a>

### Operator

Start with:

- [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md)
- [Project Structure And User Manual](282_project_structure_and_user_manual.md)
- [Generated Reports Index](reports/README.md)

Use these when you need to run the frontend, compare tracks, inspect artifacts, and review current evidence.

Evidence next:

- [Frontend Evidence Checklist](reports/README.md#frontend-evidence-checklist)

Operator quick verification:

| If you need to... | Run this first | Then check |
| --- | --- | --- |
| launch Graph Lab locally | `PY_BIN=.venv/bin/python scripts/run_graph_lab_local.sh 8081 8101` | [Frontend Evidence Checklist](reports/README.md#frontend-evidence-checklist) |
| validate the frontend/backend API path | `PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py` | [Frontend Evidence Checklist](reports/README.md#frontend-evidence-checklist) |
| validate Graph Lab browser flow end-to-end | `PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers PYTHONPATH=src .venv/bin/python scripts/validate_graph_lab_playwright_e2e.py --require-playwright --output-json docs/reports/graph_lab_playwright_e2e_latest.json` | [Frontend Evidence Checklist](reports/README.md#frontend-evidence-checklist) |

<a id="role-classic-dashboard-user"></a>

### Classic Dashboard User

Start with:

- [Frontend Dashboard Usage](116_frontend_dashboard_usage.md)
- [Project Structure And User Manual](282_project_structure_and_user_manual.md)
- [Generated Reports Index](reports/README.md)

Use these when you need the lightweight dashboard shell, a quick demo route, or a simple presentation-oriented frontend path.

Evidence next:

- [Frontend Evidence Checklist](reports/README.md#frontend-evidence-checklist)

Classic Dashboard quick verification:

| If you need to... | Run this first | Then check |
| --- | --- | --- |
| launch the classic dashboard locally | `PY_BIN=.venv/bin/python scripts/run_web_e2e_dashboard_local.sh 8080 8099` | [Frontend Evidence Checklist](reports/README.md#frontend-evidence-checklist) |
| validate the dashboard/backend API path | `PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py` | [Frontend Evidence Checklist](reports/README.md#frontend-evidence-checklist) |
| review the lightweight demo summary | `PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py` | `docs/reports/frontend_quickstart_v1.json` |

<a id="role-developer"></a>

### Developer

Start with:

- [Project Structure And User Manual](282_project_structure_and_user_manual.md)
- [Architecture](03_architecture.md)
- [Output Contracts](02_output_contracts.md)

Use these when you need repository structure, module boundaries, and implementation contracts before changing code.

Evidence next:

- [Frontend Evidence Checklist](reports/README.md#frontend-evidence-checklist)
- [RadarSimPy Evidence Checklist](reports/README.md#radarsimpy-evidence-checklist)
- [PO-SBR Evidence Checklist](reports/README.md#po-sbr-evidence-checklist)

Developer quick verification:

| If you changed... | Run this first | Then check |
| --- | --- | --- |
| `frontend/graph_lab`, web orchestrator, or dashboard wiring | `PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py` | [Frontend Evidence Checklist](reports/README.md#frontend-evidence-checklist) |
| Graph Lab browser UX or interaction flow | `PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers PYTHONPATH=src .venv/bin/python scripts/validate_graph_lab_playwright_e2e.py --require-playwright --output-json docs/reports/graph_lab_playwright_e2e_latest.json` | [Frontend Evidence Checklist](reports/README.md#frontend-evidence-checklist) |
| RadarSimPy wrapper/runtime coupling | `PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_wrapper_integration_gate.py --output-summary-json docs/reports/radarsimpy_wrapper_integration_gate_manual.json` | [RadarSimPy Evidence Checklist](reports/README.md#radarsimpy-evidence-checklist) |
| paid RadarSimPy production path | `PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_paid_6m_gate_ci.sh` | [RadarSimPy Evidence Checklist](reports/README.md#radarsimpy-evidence-checklist) |
| release-candidate validation subset | `PYTHONPATH=src .venv/bin/python scripts/run_canonical_release_candidate_subset.py --output-json docs/reports/canonical_release_candidate_subset_latest.json` | [Generated Reports Index](reports/README.md) |
| PO-SBR runtime-affecting path | `PYTHONPATH=src .venv/bin/python scripts/run_po_sbr_post_change_gate.py --strict` | [PO-SBR Evidence Checklist](reports/README.md#po-sbr-evidence-checklist) |

<a id="role-validator"></a>

### Validator

Start with:

- [Validation Checkpoints](04_validation_checkpoints.md)
- [Generated Reports Index](reports/README.md)
- [Scene Backend Golden Path Contract](251_scene_backend_golden_path_contract.md)

Use these when you need pass/fail criteria, current evidence, and stable validation expectations.

Evidence next:

- [RadarSimPy Evidence Checklist](reports/README.md#radarsimpy-evidence-checklist)
- [PO-SBR Evidence Checklist](reports/README.md#po-sbr-evidence-checklist)

Validator quick verification:

| If you need to verify... | Run this first | Then check |
| --- | --- | --- |
| frontend/backend API contract health | `PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py` | [Frontend Evidence Checklist](reports/README.md#frontend-evidence-checklist) |
| Graph Lab browser-level operator flow | `PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers PYTHONPATH=src .venv/bin/python scripts/validate_graph_lab_playwright_e2e.py --require-playwright --output-json docs/reports/graph_lab_playwright_e2e_latest.json` | [Frontend Evidence Checklist](reports/README.md#frontend-evidence-checklist) |
| RadarSimPy wrapper gate only | `PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_wrapper_integration_gate.py --output-summary-json docs/reports/radarsimpy_wrapper_integration_gate_manual.json` | [RadarSimPy Evidence Checklist](reports/README.md#radarsimpy-evidence-checklist) |
| RadarSimPy smoke gate only | `PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_integration_smoke_gate.py --output-summary-json docs/reports/radarsimpy_integration_smoke_gate_manual.json` | [RadarSimPy Evidence Checklist](reports/README.md#radarsimpy-evidence-checklist) |
| PO-SBR runtime-affecting closure gate | `PYTHONPATH=src .venv/bin/python scripts/run_po_sbr_post_change_gate.py --strict` | [PO-SBR Evidence Checklist](reports/README.md#po-sbr-evidence-checklist) |

<a id="role-paid-radarsimpy-validator"></a>

### Paid RadarSimPy Validator

Start with:

- [RadarSimPy Runtime](285_install_radarsimpy_runtime.md)
- [Validation Checkpoints](04_validation_checkpoints.md)
- [Generated Reports Index](reports/README.md)

Use these when you need the production-license path, paid runtime gates, readiness checks, and final RadarSimPy evidence.

Evidence next:

- [RadarSimPy Evidence Checklist](reports/README.md#radarsimpy-evidence-checklist)

Paid RadarSimPy quick verification:

| If you need to verify... | Run this first | Then check |
| --- | --- | --- |
| full paid production gate chain | `PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_paid_6m_gate_ci.sh` | [RadarSimPy Evidence Checklist](reports/README.md#radarsimpy-evidence-checklist) |
| wrapper integration before the full chain | `PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_wrapper_integration_gate.py --output-summary-json docs/reports/radarsimpy_wrapper_integration_gate_manual.json` | [RadarSimPy Evidence Checklist](reports/README.md#radarsimpy-evidence-checklist) |
| smoke gate before the full chain | `PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_integration_smoke_gate.py --output-summary-json docs/reports/radarsimpy_integration_smoke_gate_manual.json` | [RadarSimPy Evidence Checklist](reports/README.md#radarsimpy-evidence-checklist) |

## Installation

Read in this order:

1. [Install Onboarding Map](288_install_onboarding_map.md)
2. [Install Guide: Base Environment](284_install_base_environment.md)
3. one runtime-specific guide if needed:
   - [RadarSimPy Runtime](285_install_radarsimpy_runtime.md)
   - [Sionna-Style RT Runtime](286_install_sionna_style_rt_runtime.md)
   - [PO-SBR Runtime](287_install_po_sbr_runtime.md)

## Usage And Frontend

Start with:

- [Project Structure And User Manual](282_project_structure_and_user_manual.md)
- [프로젝트 구조 및 사용자 매뉴얼](283_project_structure_and_user_manual_ko.md)
- [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md)
- [Frontend Dashboard Usage](116_frontend_dashboard_usage.md)

## Architecture And Core Contracts

Start with:

- [Architecture](03_architecture.md)
- [Output Contracts](02_output_contracts.md)
- [AVX Lite Open Source Architecture Spec](267_avx_lite_open_source_architecture_spec.md)
- [Frontend Runtime Multiplexing And LGIT](278_frontend_runtime_multiplexing_and_lgit.md)

## Validation And Gates

Start with:

- [Validation Checkpoints](04_validation_checkpoints.md)
- [Canonical Validation Scenario Pack](289_canonical_validation_scenario_pack.md)
- [Parity Metrics Contract](13_parity_metrics_contract.md)
- [Multi-Backend Parity Harness Contract](92_multi_backend_parity_harness_contract.md)
- [Scene Backend Golden Path Contract](251_scene_backend_golden_path_contract.md)

## Release Notes And Generated Reports

Start with:

- [Generated Reports Index](reports/README.md)
- [Release Notes: RadarSimPy Frontend Multiplexing](279_release_notes_radarsimpy_frontend_multiplexing_2026_03_05.md)
- [Release One-Pager](280_release_one_pager_radarsimpy_2026_03_05.md)
- [Release One-Pager (Korean)](281_release_one_pager_radarsimpy_2026_03_05_ko.md)
- [Release Announcement Templates](282_release_announcement_templates_2026_03_05.md)

## How To Read The Numbered Docs

- `01` to `099`
  - early architecture, ingest, parity, and data contracts
- `100` to `199`
  - runtime, web API, and frontend contract evolution
- `200` to `279`
  - rollout, hardening, and release preparation records
- `280+`
  - current user manuals, install guides, onboarding, and release-facing summaries

Do not assume the latest-numbered file is the best starting point. Use the five sections above first, then open older numbered docs only when you need contract history or a specific subsystem record.
