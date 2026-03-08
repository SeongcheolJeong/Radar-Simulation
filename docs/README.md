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
| validate paid RadarSimPy production access | [RadarSimPy Runtime](285_install_radarsimpy_runtime.md) | `scripts/run_radarsimpy_paid_6m_gate_ci.sh` |
| review release-facing evidence | [Generated Reports Index](reports/README.md) | release notes and one-pagers |

## By Role

### Operator

Start with:

- [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md)
- [Project Structure And User Manual](282_project_structure_and_user_manual.md)
- [Generated Reports Index](reports/README.md)

Use these when you need to run the frontend, compare tracks, inspect artifacts, and review current evidence.

### Classic Dashboard User

Start with:

- [Frontend Dashboard Usage](116_frontend_dashboard_usage.md)
- [Project Structure And User Manual](282_project_structure_and_user_manual.md)
- [Generated Reports Index](reports/README.md)

Use these when you need the lightweight dashboard shell, a quick demo route, or a simple presentation-oriented frontend path.

### Developer

Start with:

- [Project Structure And User Manual](282_project_structure_and_user_manual.md)
- [Architecture](03_architecture.md)
- [Output Contracts](02_output_contracts.md)

Use these when you need repository structure, module boundaries, and implementation contracts before changing code.

### Validator

Start with:

- [Validation Checkpoints](04_validation_checkpoints.md)
- [Generated Reports Index](reports/README.md)
- [Scene Backend Golden Path Contract](251_scene_backend_golden_path_contract.md)

Use these when you need pass/fail criteria, current evidence, and stable validation expectations.

### Paid RadarSimPy Validator

Start with:

- [RadarSimPy Runtime](285_install_radarsimpy_runtime.md)
- [Validation Checkpoints](04_validation_checkpoints.md)
- [Generated Reports Index](reports/README.md)

Use these when you need the production-license path, paid runtime gates, readiness checks, and final RadarSimPy evidence.

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
