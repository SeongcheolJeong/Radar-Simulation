# PO-SBR Realism Threshold Hardening Contract (M14.13)

## Goal

Apply stepwise stricter KPI thresholds to realism profiles (multi-target/material/mesh) while preserving strict-gate and stability evidence from previous full-track campaigns.

## Scope

- hardening runner: `scripts/run_po_sbr_realism_threshold_hardening_campaign.py`
- hardening validator: `scripts/validate_po_sbr_realism_threshold_hardening_report.py`
- deterministic runner validation: `scripts/validate_run_po_sbr_realism_threshold_hardening_campaign.py`

## Inputs

1. full-track bundle report (`full_track_status=ready`)
2. stability campaign report (`campaign_status=stable`) (optional but recommended and used in M14.13)

## Threshold profiles (default)

1. `realism_tight_v1`
2. `realism_tight_v2`
3. `realism_tight_v3`

## Runner Contract

### Command

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_po_sbr_realism_threshold_hardening_campaign.py \
  --strict-hardened \
  --full-track-bundle-summary-json docs/reports/po_sbr_physical_full_track_bundle_local_2026_03_01.json \
  --stability-summary-json docs/reports/po_sbr_physical_full_track_stability_local_2026_03_01.json \
  --output-root data/runtime_golden_path/po_sbr_realism_threshold_hardening_local_2026_03_01 \
  --output-summary-json docs/reports/po_sbr_realism_threshold_hardening_local_2026_03_01.json
```

### Required output keys

- top-level:
  - `version`
  - `generated_at_utc`
  - `workspace_root`
  - `hardening_status` (`hardened|blocked`)
  - `blockers`
  - `source_full_track_bundle_summary_json`
  - `source_stability_summary_json`
  - `source_full_track_status`
  - `source_stability_status`
  - `threshold_profiles`
  - `realism_profile_names`
  - `profiles`
  - `summary`
- per-threshold-profile:
  - `threshold_profile`
  - `thresholds_json`
  - `thresholds`
  - `status` (`ready|blocked|failed`)
  - `summary`
  - `rows`
- per-row:
  - `profile`
  - `profile_family`
  - `source_golden_summary_json`
  - `thresholds_json`
  - `output_kpi_json`
  - `run_kpi`
  - `validate_kpi`
  - `run_ok`
  - `campaign_status`
  - `blockers`
  - `parity_fail_count`
  - `parity_fail_pairs`

## Status semantics

- `hardening_status=hardened`
  - full-track source is ready
  - optional stability source is stable (if provided)
  - realism profiles are found
  - all threshold profiles are `ready`
- `hardening_status=blocked`
  - any of the above fails

`--strict-hardened` behavior:

- report is written first
- command exits non-zero when `hardening_status != hardened`

## Validation

### 1) Hardening report validator

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_realism_threshold_hardening_report.py \
  --summary-json docs/reports/po_sbr_realism_threshold_hardening_local_2026_03_01.json \
  --require-hardened
```

### 2) Deterministic runner validation

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_run_po_sbr_realism_threshold_hardening_campaign.py
```

## Acceptance

M14.13 is accepted only if:

1. hardening report is generated from local full-track/stability evidence
2. all default hardening threshold profiles are ready
3. no parity failures remain under hardening threshold profiles
4. hardening validator and deterministic runner validation both pass
