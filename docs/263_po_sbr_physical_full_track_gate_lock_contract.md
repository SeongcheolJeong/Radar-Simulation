# PO-SBR Physical Full-Track Gate Lock Contract (M14.14)

## Goal

Provide a single local command to produce radar-developer gate evidence by chaining:

1. repeated physical full-track stability campaign, then
2. realism KPI hardening with promoted gate candidate.

## Scope

- gate-lock runner: `scripts/run_po_sbr_physical_full_track_gate_lock.py`
- gate-lock validator: `scripts/validate_po_sbr_physical_full_track_gate_lock_report.py`
- deterministic runner validation: `scripts/validate_run_po_sbr_physical_full_track_gate_lock.py`

## Inputs

1. full-track bundle report (`full_track_status=ready`)
2. local runtime execution context on this Linux PC (`.venv-po-sbr`)
3. optional reused evidence reports:
   - stability summary (`campaign_status=stable`)
   - hardening summary (`hardening_status=hardened`, candidate ready)

## Runner Contract

### Command (chained execution mode)

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_po_sbr_physical_full_track_gate_lock.py \
  --strict-ready \
  --full-track-bundle-summary-json docs/reports/po_sbr_physical_full_track_bundle_local_2026_03_01.json \
  --output-root data/runtime_golden_path/po_sbr_physical_full_track_gate_lock_local_2026_03_01 \
  --output-summary-json docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01.json \
  --stability-runs 3 \
  --threshold-profile realism_tight_v2 \
  --realism-gate-candidate realism_tight_v2
```

### Command (reuse validated evidence mode)

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_po_sbr_physical_full_track_gate_lock.py \
  --strict-ready \
  --full-track-bundle-summary-json docs/reports/po_sbr_physical_full_track_bundle_local_2026_03_01.json \
  --reuse-stability-summary-json docs/reports/po_sbr_physical_full_track_stability_local_2026_03_01_r3.json \
  --reuse-hardening-summary-json docs/reports/po_sbr_realism_threshold_hardening_local_2026_03_01_gate_lock_v2.json \
  --output-root data/runtime_golden_path/po_sbr_physical_full_track_gate_lock_local_2026_03_01 \
  --output-summary-json docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01.json \
  --stability-runs 3 \
  --threshold-profile realism_tight_v2 \
  --realism-gate-candidate realism_tight_v2
```

### Required output keys

- top-level:
  - `version`
  - `generated_at_utc`
  - `workspace_root`
  - `gate_lock_status` (`ready|blocked`)
  - `blockers`
  - `full_track_bundle_summary_json`
  - `realism_gate_candidate`
  - `threshold_profiles`
  - `stability`
  - `hardening`
  - `summary`
- `stability`:
  - `run`
  - `summary_json`
  - `campaign_status`
  - `summary`
- `hardening`:
  - `run`
  - `summary_json`
  - `hardening_status`
  - `realism_gate_candidate`
  - `realism_gate_candidate_status`
  - `summary`

## Status semantics

- `gate_lock_status=ready`
  - stability phase is stable (`campaign_status=stable`) from executed or reused report
  - hardening phase is hardened (`hardening_status=hardened`) from executed or reused report
  - hardening report candidate matches requested candidate
  - `realism_gate_candidate_status=ready`
  - no blockers
- `gate_lock_status=blocked`
  - any of the above fails

`--strict-ready` behavior:

- report is written first
- command exits non-zero when `gate_lock_status != ready`

## Validation

### 1) Gate-lock report validator

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_po_sbr_physical_full_track_gate_lock_report.py \
  --summary-json docs/reports/po_sbr_physical_full_track_gate_lock_local_2026_03_01.json \
  --require-ready
```

### 2) Deterministic runner validation

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_run_po_sbr_physical_full_track_gate_lock.py
```

## Acceptance

M14.14 is accepted only if:

1. gate-lock report is generated locally from full-track input
2. stability/hardening phases are proven either by chained execution mode or by reused validated local evidence reports
3. promoted candidate (`realism_tight_v2`) is `ready`
4. report validator and deterministic runner validation both pass
