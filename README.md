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

Run motion compensation core validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_motion_compensation_core.py
```

Run ingest CLI motion compensation validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_motion_comp.py
```

Run ingest CLI scenario profile defaults validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_profile_defaults.py
```

Run moving-target replay batch validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_moving_target_replay_batch.py
```

Run profile-lock finalization validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_profile_lock_finalization.py
```

Run measured replay orchestration validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_measured_replay_execution.py
```

Run measured replay plan builder validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_measured_replay_plan_builder.py
```

Run replay manifest builder validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_replay_manifest_builder.py
```

Run mock measured packs end-to-end validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mock_measured_packs_e2e.py
```

Run ADC pack builder validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_adc_pack_builder.py
```

Run MAT ADC extractor core validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mat_adc_extractor_core.py
```

Run one-command onboarding pipeline validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_dataset_onboarding_pipeline.py
```

Run profile-from-pack rebuild validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_build_scenario_profile_from_pack.py
```

Rebuild scenario profile from a measured pack using versioned policy:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/build_scenario_profile_from_pack.py \
  --pack-root /path/to/pack_root \
  --policy-json /Users/seongcheoljeong/Documents/Codex_test/configs/profile_tuning/xiangyu_raw_adc_v1.json \
  --emit-policy-json /path/to/pack_root/profile_tuning_policy.json \
  --backup-original
```

Run parity metrics contract validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_parity_metrics_contract.py
```

Run path-power tuning validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_tuning.py
```

Run parity drift analysis validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_parity_drift_analysis.py
```

Run cross-family parity shift validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_cross_family_parity_shift.py
```

Run ingest CLI path-power fit validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_path_power_fit.py
```

Run end-to-end path-power fit cycle validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_cycle.py
```

Run path-power fit batch validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_batch.py
```

Run Xiangyu label->path-power CSV validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_samples_from_xiangyu_labels.py
```

Run Xiangyu label fit experiment validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_xiangyu_label_fit_experiment.py
```

Run path-power fit selection validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_selection.py
```

Run Hybrid cross-family fit comparison validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_cross_family_fit_comparison.py
```

Fit path-power parameters from measured CSV:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/fit_path_power_model_from_csv.py \
  --input-csv /path/to/path_power_samples.csv \
  --model scattering \
  --output-json /path/to/path_power_fit.json
```

Build path-power samples CSV from path list:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/build_path_power_samples_from_path_list.py \
  --input-path-list-json /path/to/path_list.json \
  --output-csv /path/to/path_power_samples.csv \
  --scenario-id demo_scenario
```

Run one-command path-power fit cycle (`baseline -> samples -> fit -> tuned`):

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/run_path_power_fit_cycle.py \
  --frames-root /path/to/frames_root \
  --radar-json /path/to/radar_parameters_hybrid.json \
  --frame-start 1 \
  --frame-end 64 \
  --camera-fov-deg 90 \
  --mode reflection \
  --file-ext .npy \
  --path-power-apply-mode replace \
  --work-root /path/to/cycle_work \
  --scenario-id cycle_demo
```

Run path-power fit batch (`multi-CSV x multi-model`):

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/run_path_power_fit_batch.py \
  --csv-case caseA=/path/to/case_a_path_power_samples.csv \
  --csv-case caseB=/path/to/case_b_path_power_samples.csv \
  --model reflection \
  --model scattering \
  --batch-id my_batch \
  --output-root /path/to/fit_batch_out \
  --output-summary-json /path/to/path_power_fit_batch_summary.json
```

Build path-power samples from Xiangyu labels + ADC:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/build_path_power_samples_from_xiangyu_labels.py \
  --adc-root /path/to/Automotive/2019_04_09_bms1000/radar_raw_frame \
  --labels-root /path/to/Automotive/2019_04_09_bms1000/text_labels \
  --output-csv /path/to/path_power_samples.csv \
  --output-meta-json /path/to/path_power_samples.meta.json \
  --scenario-id xiangyu_bms1000 \
  --adc-type mat \
  --adc-order scrt
```

Run Xiangyu label fit experiment matrix (CSV + fit batch):

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/run_xiangyu_label_fit_experiment.py \
  --case bms1000=/path/to/2019_04_09_bms1000/radar_raw_frame::/path/to/2019_04_09_bms1000/text_labels \
  --case cms1000=/path/to/2019_04_09_cms1000/radar_raw_frame::/path/to/2019_04_09_cms1000/text_labels \
  --frame-counts 128,512 \
  --models reflection,scattering \
  --output-root /path/to/xiangyu_label_fit_experiment \
  --output-summary-json /path/to/xiangyu_label_fit_experiment_summary.json
```

Select/lock final fit JSONs from experiment summary:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/select_path_power_fit_from_experiment.py \
  --experiment-summary-json /path/to/xiangyu_label_fit_experiment_summary.json \
  --selection-strategy largest_frame_then_rmse \
  --output-dir /path/to/selected_fits \
  --output-summary-json /path/to/path_power_fit_selection_summary.json
```

Run Hybrid cross-family baseline vs tuned comparison:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/run_hybrid_cross_family_fit_comparison.py \
  --case-a-id case_a \
  --case-a-frames-root /path/to/case_a/frames \
  --case-a-radar-json /path/to/case_a/radar_parameters_hybrid.json \
  --case-b-id case_b \
  --case-b-frames-root /path/to/case_b/frames \
  --case-b-radar-json /path/to/case_b/radar_parameters_hybrid.json \
  --path-power-fit-json /path/to/path_power_fit_reflection_selected.json \
  --path-power-apply-mode shape_only \
  --frame-start 1 \
  --frame-end 64 \
  --camera-fov-deg 90 \
  --mode reflection \
  --file-ext .npy \
  --output-root /path/to/hybrid_cross_family_run \
  --output-summary-json /path/to/hybrid_cross_family_fit_summary.json
```

Analyze parity drift across replay reports:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/analyze_parity_drift_from_replay_reports.py \
  --report baseline=/path/to/baseline_replay_report.json \
  --report candidate=/path/to/candidate_replay_report.json \
  --output-json /path/to/parity_drift_report.json
```

Evaluate baseline/tuned cross-family parity shift:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/evaluate_cross_family_parity_shift.py \
  --baseline-a famA_base=/path/to/family_a_baseline_replay_report.json \
  --baseline-b famB_base=/path/to/family_b_baseline_replay_report.json \
  --tuned-a famA_tuned=/path/to/family_a_tuned_replay_report.json \
  --tuned-b famB_tuned=/path/to/family_b_tuned_replay_report.json \
  --metric ra_shape_nmse \
  --metric rd_shape_nmse \
  --output-json /path/to/cross_family_parity_shift.json
```

Apply fitted path-power model during ingest:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/run_hybrid_ingest_to_adc.py \
  --frames-root /path/to/render \
  --radar-json /path/to/radar_parameters_hybrid.json \
  --frame-start 1 \
  --frame-end 64 \
  --camera-fov-deg 90 \
  --mode reflection \
  --file-ext .exr \
  --path-power-fit-json /path/to/path_power_fit.json \
  --path-power-apply-mode shape_only \
  --output-dir /path/to/out
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
  --enable-motion-compensation \
  --motion-comp-fd-hz 1200 \
  --motion-comp-chirp-interval-s 6e-5 \
  --motion-comp-reference-tx 0 \
  --output-dir /path/to/out
```

Use scenario profile defaults in ingest:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/run_hybrid_ingest_to_adc.py \
  --frames-root /path/to/render \
  --radar-json /path/to/radar_parameters_hybrid.json \
  --frame-start 1 \
  --frame-end 64 \
  --camera-fov-deg 90 \
  --mode reflection \
  --file-ext .exr \
  --scenario-profile-json /path/to/scenario_profile.json \
  --run-hybrid-estimation \
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

Build profile with motion tuning manifest:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/build_scenario_profile.py \
  --scenario-id moving_target_v1 \
  --samples-npz /path/to/calibration_samples.npz \
  --reference-estimation-npz /path/to/reference_hybrid_estimation.npz \
  --motion-tuning-manifest-json /path/to/motion_tuning_manifest.json \
  --output-profile-json /path/to/scenario_profile.json
```

Run moving-target replay batch:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/run_moving_target_replay_batch.py \
  --manifest-json /path/to/replay_manifest.json \
  --output-json /path/to/replay_report.json
```

Finalize scenario profile lock from replay report:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/finalize_scenario_profile_lock.py \
  --replay-report-json /path/to/replay_report.json \
  --output-lock-json /path/to/profile_lock_report.json \
  --output-locked-profile-dir /path/to/locked_profiles \
  --require-motion-defaults-enabled
```

Run measured multi-pack replay execution (`replay + lock`) in one command:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/run_measured_replay_execution.py \
  --plan-json /path/to/measured_replay_plan.json \
  --output-root /path/to/measured_replay_outputs \
  --output-summary-json /path/to/measured_replay_summary.json
```

Auto-build `measured_replay_plan.json` from pack folders:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/build_measured_replay_plan.py \
  --packs-root /path/to/packs_root \
  --output-plan-json /path/to/measured_replay_plan.json
```

Auto-build per-pack `replay_manifest.json`:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/build_replay_manifest_from_pack.py \
  --pack-root /path/to/pack_root
```

Generate mock measured packs when real data is unavailable:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/generate_mock_measured_packs.py \
  --output-root /tmp/mock_measured_packs \
  --include-failing-pack
```

Extract ADC NPZ from MAT files:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/extract_mat_adc_to_npz.py \
  --input-root /path/to/mat_root \
  --output-root /path/to/adc_npz \
  --recursive
```

Build one measured pack from ADC NPZ:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/build_pack_from_adc_npz_dir.py \
  --input-root /path/to/adc_npz \
  --input-glob \"*.npz\" \
  --output-pack-root /path/to/pack_out \
  --scenario-id my_scenario \
  --adc-order sctr
```

Run one-command onboarding (ADC NPZ input):

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/run_dataset_onboarding_pipeline.py \
  --input-type adc_npz \
  --input-root /path/to/adc_npz \
  --scenario-id dataset_v1 \
  --work-root /path/to/onboard_work \
  --adc-order sctr \
  --allow-unlocked
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

Run cross-family fit ranking validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_cross_family_ranking.py
```

Run cross-family fit-selection lock validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_selection_cross_family.py
```

Run fit-lock A/B comparison validation:

```bash
PYTHONPATH=src $PY /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_lock_ab_comparison.py
```

Fetch reference repositories:

```bash
bash /Users/seongcheoljeong/Documents/Codex_test/scripts/fetch_references.sh
```

This now also locks:

- `external/Raw_ADC_radar_dataset_for_automotive_object_detection`

Public dataset onboarding quickstart:

- `/Users/seongcheoljeong/Documents/Codex_test/docs/28_xiangyu_raw_adc_quickstart.md`

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
- `/Users/seongcheoljeong/Documents/Codex_test/docs/17_motion_compensation_contract.md`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/18_moving_target_replay_batch_contract.md`
