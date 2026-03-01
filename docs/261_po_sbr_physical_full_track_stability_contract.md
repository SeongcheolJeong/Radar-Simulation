# PO-SBR Physical Full-Track Stability Campaign Contract (M14.12)

## Goal

Verify that the local physical full-track bundle remains stable across repeated runs on this PC, and emit one campaign-level stability report for radar-developer release confidence.

## Scope

- campaign runner: `scripts/run_po_sbr_physical_full_track_stability_campaign.py`
- campaign validator: `scripts/validate_po_sbr_physical_full_track_stability_report.py`
- deterministic runner validation: `scripts/validate_run_po_sbr_physical_full_track_stability_campaign.py`

## Runner Contract

### Command

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_po_sbr_physical_full_track_stability_campaign.py \
  --strict-stable \
  --runs 2 \
  --output-root data/runtime_golden_path/po_sbr_full_track_stability_local_2026_03_01 \
  --output-summary-json docs/reports/po_sbr_physical_full_track_stability_local_2026_03_01.json
```

### Required output keys

- top-level:
  - `version`
  - `generated_at_utc`
  - `workspace_root`
  - `campaign_status` (`stable|unstable`)
  - `blockers`
  - `requested_runs`
  - `rows`
  - `summary`
- per-row:
  - `run_index`
  - `run_root`
  - `matrix_summary_json`
  - `bundle_summary_json`
  - `run_bundle`
  - `run_ok`
  - `full_track_status`
  - `matrix_status`
  - `gate_blocked_profile_count`
  - `informational_blocked_profile_count`
  - `po_sbr_executed_profile_count`
  - `required_profile_count`
  - `missing_profile_count`

## Status semantics

- `campaign_status=stable`
  - all repeated bundle runs executed successfully
  - each run has `full_track_status=ready`
  - each run has `matrix_status=ready`
  - no gate-blocked runs
- `campaign_status=unstable`
  - any stability condition above is violated

`--strict-stable` behavior:

- report is written first
- command exits non-zero when `campaign_status != stable`

## Validation

### 1) Campaign report validator

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_physical_full_track_stability_report.py \
  --summary-json docs/reports/po_sbr_physical_full_track_stability_local_2026_03_01.json \
  --require-stable
```

### 2) Deterministic runner validation

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_run_po_sbr_physical_full_track_stability_campaign.py
```

## Acceptance

M14.12 is accepted only if:

1. repeated full-track bundle campaign report is generated locally
2. campaign status is `stable` for configured run count
3. no gate-blocked runs are present
4. campaign validator and deterministic runner validation both pass
