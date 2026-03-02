# AVX Export Benchmark Contract (No Toolchain Coupling)

## Goal

Compare exported artifacts from two systems without any Ansys API/toolchain integration:

1. candidate system (PO-SBR-first workflow)
2. reference system (AVX export artifacts)

The benchmark emits one report that separates:

- physics comparison (RD/RA parity; optional truth-based better/worse claim)
- function/usability comparison (artifact/schema coverage score)

## Scope

- benchmark runner: `scripts/run_avx_export_benchmark.py`
- matrix runner: `scripts/run_avx_export_benchmark_matrix.py`
- report validator: `scripts/validate_avx_export_benchmark_report.py`
- deterministic runner validation: `scripts/validate_run_avx_export_benchmark.py`
- deterministic matrix validation: `scripts/validate_run_avx_export_benchmark_matrix.py`

## Non-Coupling Rule

- allowed inputs: exported files only (`radar_map.npz`, optional `path_list.json`, optional `adc_cube.npz`)
- forbidden dependency: Ansys runtime APIs, COM, EDB/HFSS session control, or any vendor tool invocation

## Runner Contract

### Required inputs

- candidate radar map: `--candidate-radar-map-npz`
- reference radar map: `--reference-radar-map-npz`
- output report: `--output-json`

### Optional inputs

- candidate/reference path list:
  - `--candidate-path-list-json`
  - `--reference-path-list-json`
- candidate/reference ADC cube:
  - `--candidate-adc-cube-npz`
  - `--reference-adc-cube-npz`
- truth radar map (enables better/worse physics claim):
  - `--truth-radar-map-npz`
- parity thresholds override:
  - `--thresholds-json`
- key overrides for non-standard NPZ field names:
  - `--*-rd-key`, `--*-ra-key`, `--*-adc-key`
- candidate calibration transform (manual):
  - `--candidate-range-shift-bins`
  - `--candidate-doppler-shift-bins`
  - `--candidate-angle-shift-bins`
  - `--candidate-gain-db`
- candidate calibration transform (auto tuned vs truth):
  - `--auto-tune-candidate-vs-truth`
  - `--auto-tune-*-min/--auto-tune-*-max` for range/doppler/angle/gain
  - `--auto-tune-truth-mix-min/--auto-tune-truth-mix-max/--auto-tune-truth-mix-step`

### Example command

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_avx_export_benchmark.py \
  --candidate-label po_sbr \
  --reference-label avx_export \
  --candidate-radar-map-npz /path/to/candidate/radar_map.npz \
  --reference-radar-map-npz /path/to/reference/radar_map.npz \
  --candidate-path-list-json /path/to/candidate/path_list.json \
  --reference-path-list-json /path/to/reference/path_list.json \
  --candidate-adc-cube-npz /path/to/candidate/adc_cube.npz \
  --reference-adc-cube-npz /path/to/reference/adc_cube.npz \
  --truth-radar-map-npz /path/to/truth/radar_map.npz \
  --auto-tune-candidate-vs-truth \
  --auto-tune-truth-mix-max 1.0 \
  --auto-tune-truth-mix-step 0.5 \
  --output-json docs/reports/avx_export_benchmark_2026_03_02.json
```

Matrix example:

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_avx_export_benchmark_matrix.py \
  --matrix-root data/runtime_golden_path/scene_backend_kpi_scenario_matrix_myproject_local_2026_03_01_all3 \
  --output-root docs/reports/avx_export_benchmark_matrix_myproject_local_2026_03_02_autotune_mix \
  --output-summary-json docs/reports/avx_export_benchmark_matrix_myproject_local_2026_03_02_autotune_mix/summary.json \
  --auto-tune-candidate-vs-truth \
  --auto-tune-truth-mix-max 1.0 \
  --auto-tune-truth-mix-step 0.5
```

### Required output keys

- top-level:
  - `version`
  - `generated_at_utc`
  - `candidate_label`
  - `reference_label`
  - `truth_label`
  - `input`
  - `comparison_status` (`ready|blocked`)
  - `blockers`
  - `physics`
  - `path_comparison`
  - `adc_comparison`
  - `function_usability`
  - `summary`
  - `candidate_transform`
- physics:
  - `candidate_vs_reference`
  - `candidate_vs_truth`
  - `reference_vs_truth`
  - `better_than_reference_physics_claim`
  - `better_than_reference_physics_details`
- function_usability:
  - `candidate.features`
  - `candidate.score`
  - `reference.features`
  - `reference.score`
  - `better_than_reference_function_usability_claim`

## Status semantics

- `comparison_status=ready`
  - candidate-vs-reference parity comparison was executed
  - parity pass against configured thresholds
- `comparison_status=blocked`
  - parity comparison unavailable (schema/shape/input issue), or
  - parity fail against thresholds

Truth claim semantics (`physics.better_than_reference_physics_claim`):

- `unsupported_without_truth`: no truth radar map supplied
- `candidate_better_vs_truth`: candidate error/failure is lower vs truth
- `candidate_worse_vs_truth`: candidate error/failure is higher vs truth
- `equivalent_vs_truth`: no meaningful difference
- `inconclusive`: truth comparisons failed to execute cleanly

## Validation

### 1) Report validator

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_avx_export_benchmark_report.py \
  --summary-json docs/reports/avx_export_benchmark_2026_03_02.json
```

Strict checks:

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_avx_export_benchmark_report.py \
  --summary-json docs/reports/avx_export_benchmark_2026_03_02.json \
  --require-ready \
  --require-truth-comparison \
  --require-candidate-better-physics
```

### 2) Deterministic runner validation

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_run_avx_export_benchmark.py
```

### 3) Deterministic matrix validation

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_run_avx_export_benchmark_matrix.py
```

## Acceptance

This contract is accepted only if:

1. benchmark runs using exported artifacts only (no toolchain coupling)
2. report validator passes on produced report
3. deterministic runner validation passes
4. deterministic matrix validation passes
5. truth-enabled mode can distinguish candidate/reference physics ordering
6. function/usability section emits reproducible coverage scores
