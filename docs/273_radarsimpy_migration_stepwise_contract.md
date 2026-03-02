# RadarSimPy Migration Stepwise Contract

## Purpose
Define a single orchestration run that treats `radarsimpy_rt` as reference and compares candidate backends (`analytic_targets`, `sionna_rt`, `po_sbr_rt`) step-by-step using:

- RD/RA parity (`compare_hybrid_estimation_payloads`)
- RadarSimPy-view ADC parity (`to_radarsimpy_view` + periodic-lock thresholds)

## Runner
- Script: `scripts/run_radarsimpy_migration_stepwise.py`
- Validator: `scripts/validate_run_radarsimpy_migration_stepwise.py`

## Step Flow
1. `step_0_reference_capture`: run `radarsimpy_rt` reference scene.
2. `step_1_analytic_targets`: run analytic candidate and compare to reference.
3. `step_2_sionna_rt`: run Sionna candidate and compare to reference.
4. `step_3_po_sbr_rt`: run PO-SBR candidate and compare to reference.

Each candidate step emits:
- run status (`blocked`, `executed`, or `compared`)
- runtime mode from radar-map metadata (when applicable)
- RD/RA parity payload (`pass`, `metrics`, `thresholds`, `failures`)
- ADC-view parity payload (`pass`, `metrics`, `thresholds`, `failures`)
- step gate blockers

## Scene Alignment Policy
To align one-way range across engines, Sionna sphere centers are placed at `target_range + sphere_radius` because ray intersection distance is measured to the sphere surface.

## Output Contract
Top-level summary JSON includes:
- `migration_status`: `ready` or `blocked`
- `reference`: reference execution details and gate status
- `steps[]`: per-candidate step reports
- `summary`: counts and blocker list

`ready` requires:
- reference gate pass
- all requested candidates are `compared`
- all compared candidates have `parity_pass=true`

## Exit Codes
- `0`: ready, or blocked with `--allow-failures`
- `2`: blocked without `--allow-failures`

## Validation
Deterministic validator uses fixture runtime providers and asserts both:
- all-pass ready case
- mixed blocked case with at least one parity failure

Command:

```bash
PYTHONPATH=src python3 scripts/validate_run_radarsimpy_migration_stepwise.py
```
