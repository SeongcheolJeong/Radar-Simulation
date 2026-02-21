# AVX-Style FMCW/TDM Radar Simulator (Reference Build)

This repository is being organized toward an AVX-like radar simulation pipeline:

1. Path list output (for debug and physical interpretation)
2. Raw ADC cube output (for DSP compatibility)

Current implementation status is tracked in `/Users/seongcheoljeong/Documents/Codex_test/docs/01_execution_plan.md`.

## Quick Start

Use this Python binary in this workspace:

```bash
PY=/Library/Developer/CommandLineTools/usr/bin/python3
```

Install dependency:

```bash
$PY -m pip install --user numpy
```

Run step-1 validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_step1.py
```

Run adapter smoke validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_adapter_smoke.py
```

Run Hybrid frame adapter validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_frame_adapter.py
```

Run Hybrid pipeline output validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_pipeline_output.py
```

Run P-code replacement step-1 validation (`generate_channel`):

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_generate_channel.py
```

Run P-code replacement step-2 validation (`doppler_estimation`):

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_doppler_estimation.py
```

Run P-code replacement step-3 validation (`generate_concatenated_Dop`):

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_concatenated_dop.py
```

Run P-code replacement step-4 validation (`Ang_estimation`):

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_angle_estimation.py
```

Run P-code replacement step-5 validation (`path_power` models):

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_path_power_models.py
```

Run P-code replacement step-6 validation (integrated bundle):

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_pcode_bundle.py
```

Run `.ffd` parser/interpolation validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_ffd_parser.py
```

Run real-sample `.ffd` regression validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_ffd_real_sample_regression.py
```

Run `.ffd` pipeline integration validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_ffd_pipeline_integration.py
```

Run Jones polarization flow validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_jones_polarization_flow.py
```

Run global Jones calibration validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_global_jones_calibration.py
```

Run ingest CLI global Jones integration validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_global_jones.py
```

Run calibration samples builder validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_calibration_samples_builder.py
```

Run measurement CSV converter validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_measurement_csv_converter.py
```

Run scenario profile workflow validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scenario_profile_workflow.py
```

Run parity metrics contract validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_parity_metrics_contract.py
```

Run ingest pipeline (example):

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/run_hybrid_ingest_to_adc.py \
  --frames-root /path/to/render \
  --radar-json /path/to/radar_parameters_hybrid.json \
  --frame-start 1 \
  --frame-end 64 \
  --camera-fov-deg 90 \
  --mode reflection \
  --file-ext .exr \
  --tx-ffd-glob "/path/to/tx*.ffd" \
  --rx-ffd-glob "/path/to/rx*.ffd" \
  --ffd-field-format auto \
  --use-jones-polarization \
  --global-jones-json /path/to/global_jones.json \
  --run-hybrid-estimation \
  --estimation-nfft 144 \
  --estimation-range-bin-length 10 \
  --output-dir /path/to/out
```

Fit global Jones matrix from calibration samples:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/fit_global_jones_matrix.py \
  --samples-npz /path/to/calibration_samples.npz \
  --ridge 1e-6 \
  --output-json /path/to/global_jones.json
```

Build `calibration_samples.npz` from pipeline outputs:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/build_calibration_samples_from_outputs.py \
  --path-list-json /path/to/path_list.json \
  --adc-npz /path/to/adc_cube.npz \
  --tx-ffd-glob "/path/to/tx*.ffd" \
  --rx-ffd-glob "/path/to/rx*.ffd" \
  --observed-mode normalized \
  --max-paths-per-chirp 1 \
  --output-npz /path/to/calibration_samples.npz
```

Build `calibration_samples.npz` from measured CSV:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/build_calibration_samples_from_measurement_csv.py \
  --input-csv /path/to/measurement.csv \
  --output-npz /path/to/calibration_samples.npz
```

Use column remapping when CSV headers differ:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/build_calibration_samples_from_measurement_csv.py \
  --input-csv /path/to/measurement.csv \
  --column-map-json /path/to/column_map.json \
  --output-npz /path/to/calibration_samples.npz
```

Build scenario profile (`global_jones + parity thresholds`):

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/build_scenario_profile.py \
  --scenario-id chamber_static_v1 \
  --samples-npz /path/to/calibration_samples.npz \
  --reference-estimation-npz /path/to/reference_hybrid_estimation.npz \
  --train-estimation-npz /path/to/train_candidate_1.npz \
  --train-estimation-npz /path/to/train_candidate_2.npz \
  --threshold-margin 1.5 \
  --output-profile-json /path/to/scenario_profile.json
```

Evaluate candidate with scenario profile:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/evaluate_scenario_profile.py \
  --profile-json /path/to/scenario_profile.json \
  --candidate-estimation-npz /path/to/candidate_hybrid_estimation.npz
```

Validate CLI integration with bundle:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_bundle.py
```

Validate CLI `.ffd` integration:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_ffd.py
```

Compare two `hybrid_estimation.npz` outputs:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/compare_hybrid_estimation_parity.py \
  --reference-npz /path/to/reference_hybrid_estimation.npz \
  --candidate-npz /path/to/candidate_hybrid_estimation.npz \
  --output-json /path/to/parity_report.json
```

Fetch reference repositories:

```bash
bash /Users/seongcheoljeong/Documents/Codex_test/scripts/fetch_references.sh
```

## Working Docs

- `/Users/seongcheoljeong/Documents/Codex_test/docs/01_execution_plan.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/02_output_contracts.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/03_architecture.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/04_validation_checkpoints.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/05_workflow_rules.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/06_ffd_integration_plan.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/07_reference_repo_strategy.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/08_git_workflow.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/09_hybrid_frame_adapter.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/10_hybrid_ingest_pipeline.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/11_pcode_reimplementation_plan.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/12_paper_traceability_matrix.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/13_parity_metrics_contract.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/14_jones_calibration_contract.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/15_measurement_csv_converter_contract.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/16_scenario_profile_contract.md`
