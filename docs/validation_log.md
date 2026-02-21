# Validation Log

## Entry Template

- Date:
- Command:
- Result:
- Notes:

## Latest

- Date: 2026-02-21
- Command: `PYTHONPATH=src /Library/Developer/CommandLineTools/usr/bin/python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_step1.py`
- Result: pass
- Notes:
  - CP-0 pass (ADC shape + TDM gating)
  - CP-1 pass (static target beat peak within tolerance)
  - CP-2 pass (moving target beat+doppler peak within tolerance)
  - CP-3 pass (two-path top-2 peaks detected)

## Adapter Smoke

- Date: 2026-02-21
- Command: `PYTHONPATH=src /Library/Developer/CommandLineTools/usr/bin/python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_adapter_smoke.py`
- Result: pass
- Notes:
  - Hybrid-style record mapping to canonical path contract pass
  - Canonical ADC to RadarSimPy view reshape pass

## Hybrid Frame Adapter

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_frame_adapter.py`
- Result: pass
- Notes:
  - Hybrid frame folder naming parser pass (`Tx0Rx0/AmplitudeOutput####`, `DistanceOutput####`)
  - Frame maps converted to canonical path list pass
  - Parsed paths synthesize to expected beat frequency pass

## Hybrid Pipeline Output

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_pipeline_output.py`
- Result: pass
- Notes:
  - End-to-end frame ingest pipeline pass
  - `path_list.json` + `adc_cube.npz` output generation pass
  - Metadata serialization and ADC shape check pass

## P-code Replacement P1

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_generate_channel.py`
- Result: pass
- Notes:
  - Python `generate_channel` replacement matches independent reference expression
  - Output shape check pass (`num_tx*num_rx*Np`, `Ns`)
  - Doppler mean/spread scalar equivalence pass

## P-code Replacement P2

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_doppler_estimation.py`
- Result: pass
- Notes:
  - Doppler map output shape check pass (`nfft`, `Ns`)
  - Non-window and windowed outputs both pass known-bin peak localization checks

## P-code Replacement P3

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_concatenated_dop.py`
- Result: pass
- Notes:
  - Concatenated Doppler output shape check pass (`nfft`, `1`)
  - Range-window aggregation (`max` and `average`) behavior check pass

## P-code Replacement P4

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_angle_estimation.py`
- Result: pass
- Notes:
  - Angle map output shape check pass (`nfft`, `Ns`)
  - Coarse map output shape check pass (`Ns`, `Ncap`)
  - Known spatial-bin peak localization checks pass

## P-code Replacement P5

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_path_power_models.py`
- Result: pass
- Notes:
  - Reflecting-path model monotonic range decay check pass
  - Scattering-path model angle attenuation check pass

## P-code Replacement P6

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_pcode_bundle.py`
- Result: pass
- Notes:
  - Integrated bundle path (`channel -> doppler -> concatenated -> angle`) pass
  - Output shape and finite-value checks pass for all bundle outputs

## Ingest CLI + Bundle

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_bundle.py`
- Result: pass
- Notes:
  - CLI option `--run-hybrid-estimation` wiring pass
  - Output artifacts include `hybrid_estimation.npz`

## Paper Traceability

- Date: 2026-02-21
- Command: `manual review of /Users/seongcheoljeong/Documents/Codex_test/docs/12_paper_traceability_matrix.md`
- Result: pass
- Notes:
  - Paper requirement to code/test mapping table added
  - Coverage status classified as Implemented/Partial/Planned

## FFD Parser

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_ffd_parser.py`
- Result: pass
- Notes:
  - `.ffd` parse pass for structured sample
  - periodic-phi interpolation sanity check pass

## FFD Pipeline Integration

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_ffd_pipeline_integration.py`
- Result: pass
- Notes:
  - Antenna gain scaling reflected in ADC amplitude as expected

## FFD CLI Integration

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_ffd.py`
- Result: pass
- Notes:
  - `--tx-ffd-glob/--rx-ffd-glob` CLI wiring pass
  - CLI reports `ffd enabled: True` and `jones polarization enabled: True`

## FFD Real Sample Regression

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_ffd_real_sample_regression.py`
- Result: pass
- Notes:
  - Locked reference artifact: `/Users/seongcheoljeong/Documents/Codex_test/tests/data/ffd/pyaedt_T04_test.ffd`
  - HFSS-style grid-header parser path exercised

## Jones Polarization Flow

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_jones_polarization_flow.py`
- Result: pass
- Notes:
  - Jones synthesis path check pass (`rx^H * J * tx`)
  - Path-level `pol_matrix` handling pass

## Parity Metrics Contract

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_parity_metrics_contract.py`
- Result: pass
- Notes:
  - RD/RA parity comparator computes peaks, centroid/spread, and normalized map NMSE
  - Good candidate scenario passes default thresholds
  - Bad candidate scenario fails thresholds with non-zero failure list

## Global Jones Calibration

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_global_jones_calibration.py`
- Result: pass
- Notes:
  - LS-based global Jones matrix recovery pass on synthetic noisy samples
  - CLI fitter output JSON contract (`global_jones_matrix`, `metrics`) pass

## Ingest CLI + Global Jones

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_global_jones.py`
- Result: pass
- Notes:
  - `--global-jones-json` option wiring pass
  - Global Jones gain scaling reflected in ADC amplitude as expected

## Calibration Samples Builder

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_calibration_samples_builder.py`
- Result: pass
- Notes:
  - `path_list.json + adc_cube.npz + .ffd` to `calibration_samples.npz` build pass
  - Builder output used by fitter and recovers known global Jones matrix in round-trip test

## Measurement CSV Converter

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_measurement_csv_converter.py`
- Result: pass
- Notes:
  - `measurement.csv` to `calibration_samples.npz` conversion pass
  - Column-map override path pass
  - Converted samples recover known global Jones matrix in fitting round-trip

## Scenario Profile Workflow

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scenario_profile_workflow.py`
- Result: pass
- Notes:
  - Scenario profile build pass (`global_jones + parity_thresholds`)
  - Motion tuning manifest candidate selection pass (`motion_compensation_defaults` locked)
  - Profile evaluation path pass (`good -> pass`, `bad -> fail`)
  - Threshold derivation from train candidates and reference snapshot pass

## Motion Compensation Core

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_motion_compensation_core.py`
- Result: pass
- Notes:
  - Doppler peak estimation from Hybrid `H` pass
  - TDM slot phase compensation restores reference angle peak in synthetic scenario

## Ingest CLI + Motion Compensation

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_motion_comp.py`
- Result: pass
- Notes:
  - `--enable-motion-compensation` CLI wiring pass
  - Motion compensation metadata/prints present in CLI output

## Ingest CLI + Scenario Profile Defaults

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_profile_defaults.py`
- Result: pass
- Notes:
  - `--scenario-profile-json` path applies profile global Jones and motion defaults
  - Explicit pipeline run works without extra calibration/motion flags

## Moving-Target Replay Batch

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_moving_target_replay_batch.py`
- Result: pass
- Notes:
  - Replay manifest batch evaluation pass
  - Exit code policy pass (`failures -> 2`, `--allow-failures -> 0`)

## Profile Lock Finalization

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_profile_lock_finalization.py`
- Result: pass
- Notes:
  - Replay report to lock-report policy evaluation pass
  - Strict mode exit code pass (`unlocked exists -> 2`)
  - `--allow-unlocked` exit code pass (`0`)
  - `*.locked.json` output includes expected `profile_lock` metadata

## Measured Replay Execution

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_measured_replay_execution.py`
- Result: pass
- Notes:
  - Multi-pack plan parsing and execution pass
  - Per-pack artifact generation pass (`replay_report.json`, `profile_lock_report.json`, `locked_profiles/*.locked.json`)
  - Strict mode exit code pass (`unlocked pack exists -> 2`)
  - `--allow-unlocked` exit code pass (`0`)

## Measured Replay Plan Builder

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_measured_replay_plan_builder.py`
- Result: pass
- Notes:
  - Pack directory discovery pass (`replay_manifest.json` scan)
  - Optional per-pack `lock_policy.json` merge pass
  - Empty-root failure pass (without `--allow-empty`)
  - Empty-root success pass (with `--allow-empty`)

## Replay Manifest Builder

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_replay_manifest_builder.py`
- Result: pass
- Notes:
  - Per-pack replay manifest generation pass
  - Candidate discovery and naming pass
  - Sidecar metadata injection pass
  - Empty-candidate failure/success policy pass

## Mock Measured Packs E2E

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mock_measured_packs_e2e.py`
- Result: pass
- Notes:
  - Mock pack generation pass
  - Plan build + execution pass (all-pack lock success case)
  - Strict mode exit code pass (`failing-pack -> 2`)

## ADC Pack Builder

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_adc_pack_builder.py`
- Result: pass
- Notes:
  - ADC NPZ to measured-pack conversion pass
  - Candidate estimation NPZ (`fx_dop_win`, `fx_ang`) generation pass
  - Pack artifact generation pass (`scenario_profile.json`, `lock_policy.json`, `replay_manifest.json`)

## MAT ADC Extractor Core

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mat_adc_extractor_core.py`
- Result: pass
- Notes:
  - 4D numeric variable auto-selection pass
  - explicit variable selection pass
  - invalid variable/error-path checks pass

## Dataset Onboarding Pipeline

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_dataset_onboarding_pipeline.py`
- Result: pass
- Notes:
  - One-command onboarding path pass (`adc_npz -> pack -> plan -> replay`)
  - Work-root artifacts generated as expected (`onboarding_summary.json`, replay outputs)

## Public Dataset Onboarding (Xiangyu BMS1000 subset)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_dataset_onboarding_pipeline.py --input-type mat --input-root /Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_bms1000/radar_raw_frame --scenario-id xiangyu_2019_04_09_bms1000_v1 --work-root /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run1 --mat-glob "*.mat" --max-files 128 --adc-order scrt --nfft-doppler 256 --nfft-angle 64 --range-bin-limit 128 --allow-unlocked`
- Result: pass (pipeline exit code `0`)
- Notes:
  - Public raw MAT input extracted from Xiangyu zip and converted end-to-end
  - Pack generated with 128 candidates for scenario `xiangyu_2019_04_09_bms1000_v1`
  - Replay artifacts generated (`replay_report.json`, `profile_lock_report.json`, `locked_profiles/*.locked.json`)
  - Lock summary indicates unlocked case remains (expected before profile lock finalization)

## Profile Rebuild From Pack

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_build_scenario_profile_from_pack.py`
- Result: pass
- Notes:
  - Pack manifest candidate scan pass
  - Threshold derivation from candidate metrics pass
  - Policy JSON input + CLI override precedence pass
  - `profile_tuning_policy` embedding + emitted policy JSON output pass
  - Rebuilt profile parity checks pass on selected candidates

## Public Dataset Onboarding (Xiangyu BMS1000 - 512 / full)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_dataset_onboarding_pipeline.py --input-type mat --input-root /Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_bms1000/radar_raw_frame --scenario-id xiangyu_2019_04_09_bms1000_v1_512 --work-root /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512 --mat-glob "*.mat" --max-files 512 --adc-order scrt --nfft-doppler 256 --nfft-angle 64 --range-bin-limit 128 --allow-unlocked`
- Result: pass (pipeline exit code `0`)
- Notes:
  - Candidate count: 512
  - Baseline replay summary: `pass=1`, `fail=511`, `overall_lock_pass=false`
  - Tuned profile strict replay summary: `locked=1`, `unlocked=0`, `overall_lock_pass=true`

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_dataset_onboarding_pipeline.py --input-type mat --input-root /Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_bms1000/radar_raw_frame --scenario-id xiangyu_2019_04_09_bms1000_v1_full897 --work-root /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run3_full897 --mat-glob "*.mat" --adc-order scrt --nfft-doppler 256 --nfft-angle 64 --range-bin-limit 128 --allow-unlocked`
- Result: pass (pipeline exit code `0`)
- Notes:
  - Candidate count: 897
  - Baseline replay summary: `pass=1`, `fail=896`, `overall_lock_pass=false`
  - Tuned profile strict replay summary: `locked=1`, `unlocked=0`, `overall_lock_pass=true`

## Public Dataset Onboarding (Xiangyu CMS1000 - 128)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_dataset_onboarding_pipeline.py --input-type mat --input-root /Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_cms1000/radar_raw_frame --scenario-id xiangyu_2019_04_09_cms1000_v1_128 --work-root /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128 --mat-glob "*.mat" --max-files 128 --adc-order scrt --nfft-doppler 256 --nfft-angle 64 --range-bin-limit 128 --allow-unlocked`
- Result: pass (pipeline exit code `0`)
- Notes:
  - Candidate count: 128
  - Baseline replay summary: `pass=11`, `fail=117`, `overall_lock_pass=false`
  - Tuned profile strict replay summary: `locked=1`, `unlocked=0`, `overall_lock_pass=true`

## Xiangyu Policy-Governed Strict Replay

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_scenario_profile_from_pack.py --pack-root <pack> --policy-json /Users/seongcheoljeong/Documents/Codex_test/configs/profile_tuning/xiangyu_raw_adc_v1.json --emit-policy-json <pack>/profile_tuning_policy.json --backup-original`
- Result: pass
- Notes:
  - Policy-driven profile rebuild pass on BMS1000 (`512`, `897`) and CMS1000 (`128`)
  - Emitted `profile_tuning_policy.json` persisted per pack for replay reproducibility

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_measured_replay_execution.py --plan-json <run>/measured_replay_plan.json --output-root <run>/measured_replay_outputs_policy_strict --output-summary-json <run>/measured_replay_summary_policy_strict.json`
- Result: pass
- Notes:
  - BMS1000 (`512`) strict replay lock pass (`locked=1`, `unlocked=0`)
  - BMS1000 (`897`) strict replay lock pass (`locked=1`, `unlocked=0`)
  - CMS1000 (`128`) strict replay lock pass (`locked=1`, `unlocked=0`)

## Path Power Tuning

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_tuning.py`
- Result: pass
- Notes:
  - Reflection/scattering synthetic recovery pass on grid-included ground-truth parameters
  - CLI path (`fit_path_power_model_from_csv.py`) pass with CSV input

## Ingest CLI + Path Power Fit

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_path_power_fit.py`
- Result: pass
- Notes:
  - `--path-power-fit-json` CLI wiring pass
  - `shape_only` mode modifies relative path amplitudes by fitted range law
  - CLI output metadata includes fit enabled/model fields

## Path Power Samples Builder

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_samples_builder.py`
- Result: pass
- Notes:
  - `path_list.json` parsing and `range/az/el/observed_amp` conversion pass
  - amplitude sort/filter and CSV row serialization pass

## Path Power Cycle Demo

- Date: 2026-02-21
- Command: `run_hybrid_ingest_to_adc.py -> build_path_power_samples_from_path_list.py -> fit_path_power_model_from_csv.py` under `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cycle_demo`
- Result: pass
- Notes:
  - End-to-end artifact chain generated successfully
  - Demo validates workflow connectivity before real measured CSV input

## Path Power Fit Cycle Orchestration

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_cycle.py`
- Result: pass
- Notes:
  - Baseline->samples->fit->tuned orchestration pass
  - Summary JSON generation pass (`path_power_cycle_summary.json`)
  - Tuned slope became more negative than baseline in validation scenario

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_path_power_fit_cycle.py --frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cycle_demo/frames --radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cycle_demo/radar_parameters_hybrid.json --frame-start 1 --frame-end 4 --camera-fov-deg 90 --mode reflection --file-ext .npy --amplitude-threshold 0.01 --top-k-per-chirp 4 --fit-model reflection --path-power-apply-mode replace --work-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cycle_demo/cycle_run --scenario-id path_power_cycle_demo_v2 --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cycle_demo/cycle_run/path_power_cycle_summary.json`
- Result: pass
- Notes:
  - Demo cycle summary generated with `delta_log_slope=-0.745067`

## Parity Drift Analysis

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_parity_drift_analysis.py`
- Result: pass
- Notes:
  - Multi-report quantile summary pass
  - Baseline-relative metric drift ratio computation pass

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/analyze_parity_drift_from_replay_reports.py --report bms1000_512=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/measured_replay_outputs_policy_strict/pack_xiangyu_2019_04_09_bms1000_v1_512/replay_report.json --report bms1000_897=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run3_full897/measured_replay_outputs_policy_strict/pack_xiangyu_2019_04_09_bms1000_v1_full897/replay_report.json --report cms1000_128=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/measured_replay_outputs_policy_strict/pack_xiangyu_2019_04_09_cms1000_v1_128/replay_report.json --output-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/parity_drift_xiangyu_policy_strict_2026_02_21.json`
- Result: pass
- Notes:
  - Drift report generated for same-family (`bms1000_512` vs `bms1000_897`) and cross-family (`cms1000_128`) comparison
  - Cross-family RA shape drift identified as dominant signal
