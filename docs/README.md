# Documentation Index

## Purpose

This page is the documentation hub for the `docs/` directory.

Use it when you need to find the right document quickly instead of reading numbered design or contract files in sequence.

For repository summary, start at:

- [English Landing Page](../README.md)
- [Korean Landing Page](../README_ko.md)

For generated evidence and outputs, use:

- [Generated Reports Index](reports/README.md)

## Quick Routing

| If you want to... | Read this first | Then use |
| --- | --- | --- |
| understand the repository | [Project Structure And User Manual](282_project_structure_and_user_manual.md) | [Architecture](03_architecture.md) |
| install only what you need | [Install Onboarding Map](288_install_onboarding_map.md) | one of `284` to `287` |
| run the frontend | [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md) | `scripts/run_graph_lab_local.sh` |
| validate backend/runtime behavior | [Validation Checkpoints](04_validation_checkpoints.md) | validators and gates in `scripts/` |
| review release-facing evidence | [Generated Reports Index](reports/README.md) | release notes and one-pagers |

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
