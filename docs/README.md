# Documentation Index

## Purpose

This page is the documentation hub for the `docs/` directory.

Use it when you need to find the right document quickly instead of reading numbered design or contract files in sequence.

If you are new to the repository, start here:

- [English Landing Page](../README.md)
- [Korean Landing Page](../README_ko.md)
- [Project Structure And User Manual](282_project_structure_and_user_manual.md)
- [프로젝트 구조 및 사용자 매뉴얼](283_project_structure_and_user_manual_ko.md)
- [Install Onboarding Map](288_install_onboarding_map.md)

## Recommended Paths By Goal

| Goal | Read first | Then use |
| --- | --- | --- |
| I want to understand the whole repository | [Project Structure And User Manual](282_project_structure_and_user_manual.md) | [Architecture](03_architecture.md) |
| I want to install only what I need | [Install Onboarding Map](288_install_onboarding_map.md) | one of `284` to `287` |
| I want to run the frontend | [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md) | `scripts/run_graph_lab_local.sh` |
| I want backend or parity validation | [Validation Checkpoints](04_validation_checkpoints.md) | validator and gate scripts in `scripts/` |
| I want release or operator-facing outputs | [Release Notes](279_release_notes_radarsimpy_frontend_multiplexing_2026_03_05.md) | `docs/reports/` and release one-pagers |

## Start Here

- [English Landing Page](../README.md)
- [Korean Landing Page](../README_ko.md)
- [Project Structure And User Manual](282_project_structure_and_user_manual.md)
- [프로젝트 구조 및 사용자 매뉴얼](283_project_structure_and_user_manual_ko.md)
- [Install Onboarding Map](288_install_onboarding_map.md)

## Installation

- [Install Onboarding Map](288_install_onboarding_map.md)
- [Install Guide: Base Environment](284_install_base_environment.md)
- [Install Guide: RadarSimPy Runtime](285_install_radarsimpy_runtime.md)
- [Install Guide: Sionna-Style RT Runtime](286_install_sionna_style_rt_runtime.md)
- [Install Guide: PO-SBR Runtime](287_install_po_sbr_runtime.md)

## Usage And Frontend

- [Frontend Dashboard Usage](116_frontend_dashboard_usage.md)
- [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md)
- [Project Structure And User Manual](282_project_structure_and_user_manual.md)
- [프로젝트 구조 및 사용자 매뉴얼](283_project_structure_and_user_manual_ko.md)

## Architecture And Core Contracts

- [Architecture](03_architecture.md)
- [Output Contracts](02_output_contracts.md)
- [AVX Lite Open Source Architecture Spec](267_avx_lite_open_source_architecture_spec.md)
- [Frontend Runtime Multiplexing And LGIT](278_frontend_runtime_multiplexing_and_lgit.md)

## Validation And Gates

- [Validation Checkpoints](04_validation_checkpoints.md)
- [Parity Metrics Contract](13_parity_metrics_contract.md)
- [Multi-Backend Parity Harness Contract](92_multi_backend_parity_harness_contract.md)
- [Scene Backend Golden Path Contract](251_scene_backend_golden_path_contract.md)
- [Compare History Bundle Schema Migration](281_compare_history_bundle_schema_migration.md)

## Release Notes And Generated Reports

- static docs index: this page
- generated reports index: [Generated Reports Index](reports/README.md)
- [Release Notes: RadarSimPy Frontend Multiplexing](279_release_notes_radarsimpy_frontend_multiplexing_2026_03_05.md)
- [Release One-Pager](280_release_one_pager_radarsimpy_2026_03_05.md)
- [Release One-Pager (Korean)](281_release_one_pager_radarsimpy_2026_03_05_ko.md)
- [Release Announcement Templates](282_release_announcement_templates_2026_03_05.md)
- generated reports and screenshots: `docs/reports/`
- stable report entry points:
  - `docs/reports/frontend_quickstart_v1.json`
  - `docs/reports/graph_lab_playwright_e2e_latest.json`
  - `docs/reports/radarsimpy_final_status_latest.json`
  - `docs/reports/graph_lab_playwright_snapshots/latest/`

## How To Read The Numbered Docs

- `01` to `099`
  - early architecture, ingest, parity, and data contracts
- `100` to `199`
  - runtime, web API, and frontend contract evolution
- `200` to `279`
  - rollout, hardening, and release preparation records
- `280+`
  - current user manuals, install guides, onboarding, and release-facing summaries

Do not assume the latest-numbered file is always the best starting point. Use the sections above to choose by purpose.
