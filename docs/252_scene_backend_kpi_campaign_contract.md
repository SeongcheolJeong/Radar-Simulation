# Scene Backend KPI Campaign Contract (M14.8)

## Goal

Convert backend runtime execution outputs into a radar-developer KPI/parity campaign report using shared RD/RA parity metrics.

Inputs:

1. `analytic_targets` runtime output
2. `sionna_rt` runtime output
3. `po_sbr_rt` runtime output

Source report is produced by:

- `scripts/run_scene_backend_golden_path.py`

## Scope

- campaign runner: `scripts/run_scene_backend_kpi_campaign.py`
- report validator: `scripts/validate_scene_backend_kpi_campaign_report.py`
- deterministic runner validation: `scripts/validate_run_scene_backend_kpi_campaign.py`

## Runner Contract

### Command

```bash
PYTHONPATH=src python3 scripts/run_scene_backend_kpi_campaign.py \
  --strict-ready \
  --golden-path-summary-json docs/reports/scene_backend_golden_path_local_2026_03_01_all3_eqv2.json \
  --output-summary-json docs/reports/scene_backend_kpi_campaign_local_2026_03_01_all3_eqv2.json
```

### Required output keys

- top-level:
  - `version`
  - `source_golden_path_summary_json`
  - `reference_backend`
  - `requested_backends`
  - `executed_backends`
  - `campaign_status`
  - `blockers`
  - `threshold_overrides`
  - `comparisons`
  - `summary`
- comparison row:
  - `reference_backend`
  - `candidate_backend`
  - `reference_status`
  - `candidate_status`
  - `compared`
  - `parity`
  - `kpi`
  - `reason`

### Status semantics

- `campaign_status=ready`
  - reference backend executed
  - at least one candidate backend compared
  - no parity failures detected under selected threshold set
- `campaign_status=blocked`
  - one or more blockers detected (`reference_backend_not_executed`, `no_comparable_candidates`, `parity_failure_detected`, ...)

`--strict-ready` behavior:

- report is written first
- command exits non-zero when `campaign_status != ready`

## Validation

### 1) Contract validator

```bash
PYTHONPATH=src python3 scripts/validate_scene_backend_kpi_campaign_report.py \
  --summary-json docs/reports/scene_backend_kpi_campaign_local_2026_03_01_all3_eqv2.json
```

### 2) Deterministic runner validation

```bash
PYTHONPATH=src python3 scripts/validate_run_scene_backend_kpi_campaign.py
```

## Acceptance

M14.8 is accepted only if:

1. KPI campaign report is generated from golden-path output
2. pairwise parity metrics are recorded per candidate backend
3. campaign-level gate status (`ready|blocked`) and blockers are explicit
4. deterministic runner validation and report schema validation both pass
