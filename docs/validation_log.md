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

## Cross-Family Parity Shift Evaluation

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_cross_family_parity_shift.py`
- Result: pass
- Notes:
  - Baseline/tuned x familyA/familyB evaluator validation pass
  - Gap reduction and pass-rate alignment checks pass on synthetic reports

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/evaluate_cross_family_parity_shift.py --baseline-a bms1000_512_base=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/measured_replay_outputs/pack_xiangyu_2019_04_09_bms1000_v1_512/replay_report.json --baseline-b cms1000_128_base=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/measured_replay_outputs/pack_xiangyu_2019_04_09_cms1000_v1_128/replay_report.json --tuned-a bms1000_512_tuned=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/measured_replay_outputs_tuned_strict_v2/pack_xiangyu_2019_04_09_bms1000_v1_512/replay_report.json --tuned-b cms1000_128_tuned=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/measured_replay_outputs_tuned_strict/pack_xiangyu_2019_04_09_cms1000_v1_128/replay_report.json --metric ra_shape_nmse --metric rd_shape_nmse --metric ra_peak_power_db_abs_error --metric rd_peak_power_db_abs_error --quantiles 0.5,0.9,0.99 --output-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/cross_family_parity_shift_xiangyu_2026_02_21.json`
- Result: pass
- Notes:
  - Pass-rate cross-family gap reduced from `0.083984` to `0.000000`
  - Selected RA/RD metric quantile cross-family gaps unchanged in this replay set

## Path Power Fit Batch

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_batch.py`
- Result: pass
- Notes:
  - Multi-case, multi-model fit batch validation pass
  - Per-case fit JSON emission and batch summary checks pass

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_path_power_fit_batch.py --csv-case demoA=/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cycle_demo/path_power_samples.csv --csv-case demoB=/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cycle_demo/cycle_run/path_power_samples.csv --model reflection --model scattering --batch-id path_power_demo_batch_v1 --top-k 10 --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cycle_demo/fit_batch_run --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_batch_demo_2026_02_21.json`
- Result: pass
- Notes:
  - Reflection/scattering batch fit summary generated (`run_count=4`)
  - Demonstrates batch experiment workflow before real measured CSV onboarding

## Xiangyu Label -> Path-Power Samples

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_samples_from_xiangyu_labels.py`
- Result: pass
- Notes:
  - `text_labels + ADC` to `path_power_samples.csv` conversion validation pass
  - Numeric frame-index matching across different filename formats pass

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_path_power_samples_from_xiangyu_labels.py --adc-root /Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_bms1000/radar_raw_frame --labels-root /Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_bms1000/text_labels --output-csv /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/bms1000_path_power_samples_128.csv --output-meta-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/bms1000_path_power_samples_128.meta.json --scenario-id xiangyu_bms1000_label_128 --adc-type mat --adc-glob "*.mat" --adc-order scrt --max-frames 128 --range-max-m 30 --nfft-range 128 --nfft-doppler 256 --nfft-angle 64 --range-bin-limit 128 --bin-search-radius 1`
- Result: pass
- Notes:
  - BMS1000 label-derived path-power CSV generated (`selected_rows=128`)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_path_power_samples_from_xiangyu_labels.py --adc-root /Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_cms1000/radar_raw_frame --labels-root /Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_cms1000/text_labels --output-csv /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/cms1000_path_power_samples_128.csv --output-meta-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/cms1000_path_power_samples_128.meta.json --scenario-id xiangyu_cms1000_label_128 --adc-type mat --adc-glob "*.mat" --adc-order scrt --max-frames 128 --range-max-m 30 --nfft-range 128 --nfft-doppler 256 --nfft-angle 64 --range-bin-limit 128 --bin-search-radius 1`
- Result: pass
- Notes:
  - CMS1000 label-derived path-power CSV generated (`selected_rows=127`)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_path_power_fit_batch.py --csv-case bms1000_128=/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/bms1000_path_power_samples_128.csv --csv-case cms1000_128=/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/cms1000_path_power_samples_128.csv --model reflection --model scattering --batch-id xiangyu_label_128_batch_v1 --top-k 10 --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/fit_batch_run --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_batch_xiangyu_labels_2026_02_21.json`
- Result: pass
- Notes:
  - Label-derived real-data batch fit summary generated (`run_count=4`)

## Xiangyu Label Fit Experiment Matrix

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_xiangyu_label_fit_experiment.py`
- Result: pass
- Notes:
  - End-to-end matrix orchestration (`CSV build + fit batch`) validation pass
  - Multi-case input and per-frame-count summary generation pass

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_xiangyu_label_fit_experiment.py --case bms1000=/Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_bms1000/radar_raw_frame::/Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_bms1000/text_labels --case cms1000=/Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_cms1000/radar_raw_frame::/Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_cms1000/text_labels --frame-counts 128,512 --models reflection,scattering --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/experiment_matrix --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/xiangyu_label_fit_experiment_128_512_2026_02_21.json --adc-type mat --adc-glob "*.mat" --adc-order scrt --nfft-range 128 --nfft-doppler 256 --nfft-angle 64 --range-bin-limit 128 --fit-top-k 10`
- Result: pass
- Notes:
  - Real Xiangyu matrix run completed for frame-counts `128,512`
  - Summary JSON emitted for case/model/frame-count comparison

## Path Power Fit Selection (Lock)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_selection.py`
- Result: pass
- Notes:
  - Model-wise fit selection logic validation pass
  - `largest_frame_then_rmse` strategy behavior validated

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/select_path_power_fit_from_experiment.py --experiment-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/xiangyu_label_fit_experiment_128_512_2026_02_21.json --selection-strategy largest_frame_then_rmse --output-dir /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_selection_xiangyu_labels_2026_02_21.json`
- Result: pass
- Notes:
  - Reflection/scattering selected fit JSONs emitted with selection metadata
  - Selected source runs: `cms1000`, frame-count `512`

## Hybrid Cross-Family Fit Comparison

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_cross_family_fit_comparison.py`
- Result: pass
- Notes:
  - `caseA reference` vs `caseB baseline/tuned` comparator validation pass
  - Metric-delta summary generation pass

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_hybrid_cross_family_fit_comparison.py --case-a-id case_a --case-a-frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/frames --case-a-radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/radar_parameters_hybrid.json --case-b-id case_b --case-b-frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/frames --case-b-radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/radar_parameters_hybrid.json --path-power-fit-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits/path_power_fit_reflection_selected.json --path-power-apply-mode shape_only --frame-start 1 --frame-end 4 --camera-fov-deg 90 --mode reflection --file-ext .npy --amplitude-threshold 0.01 --top-k-per-chirp 4 --estimation-nfft 64 --estimation-range-bin-length 8 --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/run_reflection_selected --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/hybrid_cross_family_fit_demo_reflection_2026_02_21.json`
- Result: pass
- Notes:
  - Demo report generated
  - In this setup, tuned fit increased drift (`RA/RD improved_ratio=0.0`)

## Path Power Fit Cross-Family Ranking

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_cross_family_ranking.py`
- Result: pass
- Notes:
  - Reflection/scattering ranking CLI validation pass
  - Scattering path validated with distance-prefix/scale override contract

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/rank_path_power_fits_by_cross_family.py --experiment-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/xiangyu_label_fit_experiment_128_512_2026_02_21.json --model reflection --case-a-id case_a --case-a-frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/frames --case-a-radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/radar_parameters_hybrid.json --case-b-id case_b --case-b-frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/frames --case-b-radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/radar_parameters_hybrid.json --path-power-apply-mode shape_only --frame-start 1 --frame-end 4 --camera-fov-deg 90 --file-ext .npy --amplitude-threshold 0.01 --top-k-per-chirp 4 --estimation-nfft 64 --estimation-range-bin-length 8 --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/ranking_reflection --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_cross_family_ranking_reflection_2026_02_21.json`
- Result: pass
- Notes:
  - Reflection candidates evaluated: `4/4`
  - Best fit: `cms1000_reflection (fit_128)`

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/rank_path_power_fits_by_cross_family.py --experiment-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/xiangyu_label_fit_experiment_128_512_2026_02_21.json --model scattering --case-a-id case_a --case-a-frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/frames --case-a-radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/radar_parameters_hybrid.json --case-b-id case_b --case-b-frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/frames --case-b-radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/radar_parameters_hybrid.json --path-power-apply-mode shape_only --frame-start 1 --frame-end 4 --camera-fov-deg 90 --file-ext .npy --amplitude-threshold 0.01 --top-k-per-chirp 4 --estimation-nfft 64 --estimation-range-bin-length 8 --distance-prefix DistanceOutput --distance-scale 1.0 --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/ranking_scattering --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_cross_family_ranking_scattering_2026_02_21.json`
- Result: pass
- Notes:
  - Scattering candidates evaluated: `4/4`
  - Best fit: `bms1000_scattering (fit_128)`

## Path Power Fit Selection (Cross-Family Ranking)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_selection_cross_family.py`
- Result: pass
- Notes:
  - Ranking-summary to selected-fit lock conversion validation pass
  - Selected fit metadata includes cross-family score/pass metrics

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/select_path_power_fit_from_cross_family_ranking.py --ranking-summary reflection=/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_cross_family_ranking_reflection_2026_02_21.json --ranking-summary scattering=/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_cross_family_ranking_scattering_2026_02_21.json --output-dir /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_cross_family --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_selection_cross_family_xiangyu_labels_2026_02_21.json`
- Result: pass
- Notes:
  - Cross-family locked fit set emitted for both models
  - Selection differs from RMSE-only lock for reflection and scattering

## Path Power Fit Lock A/B Comparison

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_lock_ab_comparison.py`
- Result: pass
- Notes:
  - A/B orchestrator validation pass (`rmse_lock` vs `cross_family_lock`)
  - Delta-consistency checks pass (`cross - rmse` per tuned metric)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_path_power_fit_lock_ab_comparison.py --case-a-id case_a --case-a-frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/frames --case-a-radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/radar_parameters_hybrid.json --case-b-id case_b --case-b-frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/frames --case-b-radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/radar_parameters_hybrid.json --mode reflection --rmse-fit-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits/path_power_fit_reflection_selected.json --cross-family-fit-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_cross_family/path_power_fit_reflection_selected.json --path-power-apply-mode shape_only --frame-start 1 --frame-end 4 --camera-fov-deg 90 --file-ext .npy --amplitude-threshold 0.01 --top-k-per-chirp 4 --estimation-nfft 64 --estimation-range-bin-length 8 --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/ab_lock_reflection --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_lock_ab_comparison_reflection_2026_02_21.json`
- Result: pass
- Notes:
  - Reflection A/B scores tied (`86.268252` vs `86.268252`)
  - Metric deltas (`cross - rmse`) are all zero in this demo

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_path_power_fit_lock_ab_comparison.py --case-a-id case_a --case-a-frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/frames --case-a-radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/radar_parameters_hybrid.json --case-b-id case_b --case-b-frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/frames --case-b-radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/radar_parameters_hybrid.json --mode scattering --rmse-fit-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits/path_power_fit_scattering_selected.json --cross-family-fit-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_cross_family/path_power_fit_scattering_selected.json --path-power-apply-mode shape_only --frame-start 1 --frame-end 4 --camera-fov-deg 90 --file-ext .npy --amplitude-threshold 0.01 --top-k-per-chirp 4 --estimation-nfft 64 --estimation-range-bin-length 8 --distance-prefix DistanceOutput --distance-scale 1.0 --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/ab_lock_scattering --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_lock_ab_comparison_scattering_2026_02_21.json`
- Result: pass
- Notes:
  - Scattering cross-family lock score improved (`347.609311 -> 48.288101`)
  - RA summary mean delta improved, RD summary mean delta worsened slightly

## Path Power Fit Selection (Mixed From A/B)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_fit_selection_mixed_from_ab.py`
- Result: pass
- Notes:
  - Tie-policy path (`keep_rmse`) validation pass
  - Winner-based path (`cross_family_lock`) validation pass

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/select_path_power_fit_mixed_from_ab_reports.py --ab-report reflection=/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_lock_ab_comparison_reflection_2026_02_21.json --ab-report scattering=/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_lock_ab_comparison_scattering_2026_02_21.json --rmse-selected-dir /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits --cross-selected-dir /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_cross_family --tie-policy keep_rmse --output-dir /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_selection_mixed_from_ab_xiangyu_labels_2026_02_21.json`
- Result: pass
- Notes:
  - Mixed lock emitted (`reflection <- rmse`, `scattering <- cross-family`)
  - Per-model source traceability stored in fit selection metadata

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_hybrid_cross_family_fit_comparison.py --case-a-id case_a --case-a-frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/frames --case-a-radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/radar_parameters_hybrid.json --case-b-id case_b --case-b-frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/frames --case-b-radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/radar_parameters_hybrid.json --path-power-fit-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_reflection_selected.json --path-power-apply-mode shape_only --frame-start 1 --frame-end 4 --camera-fov-deg 90 --mode reflection --file-ext .npy --amplitude-threshold 0.01 --top-k-per-chirp 4 --estimation-nfft 64 --estimation-range-bin-length 8 --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/run_reflection_mixed --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/hybrid_cross_family_fit_demo_reflection_mixed_2026_02_21.json`
- Result: pass
- Notes:
  - Mixed reflection fit comparator replay completed
  - Score-equivalent value remained `86.268252` in demo

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_hybrid_cross_family_fit_comparison.py --case-a-id case_a --case-a-frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/frames --case-a-radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/radar_parameters_hybrid.json --case-b-id case_b --case-b-frames-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/frames --case-b-radar-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/radar_parameters_hybrid.json --path-power-fit-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_scattering_selected.json --path-power-apply-mode shape_only --frame-start 1 --frame-end 4 --camera-fov-deg 90 --mode scattering --file-ext .npy --amplitude-threshold 0.01 --top-k-per-chirp 4 --estimation-nfft 64 --estimation-range-bin-length 8 --distance-prefix DistanceOutput --distance-scale 1.0 --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/run_scattering_mixed --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/hybrid_cross_family_fit_demo_scattering_mixed_2026_02_21.json`
- Result: pass
- Notes:
  - Mixed scattering fit comparator replay completed
  - Score-equivalent value remained `48.288101` in demo

## Measured Replay Fit-Change Impact Gate

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_measured_replay_fit_change_impact.py`
- Result: pass
- Notes:
  - Impact analyzer validation pass (`noop` and `impacted` synthetic plans)
  - Evidence detection for fit-reference metadata pass

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/analyze_measured_replay_fit_change_impact.py --plan-json /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run1/measured_replay_plan.json --plan-json /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/measured_replay_plan.json --plan-json /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run3_full897/measured_replay_plan.json --plan-json /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/measured_replay_plan.json --fit-dir /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits --fit-dir /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_cross_family --fit-dir /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed --output-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/measured_replay_fit_change_impact_xiangyu_2026_02_21.json`
- Result: pass
- Notes:
  - `plan_count=4`, `impacted_plan_count=0`
  - recommendation: `skip_measured_replay_rerun_due_to_no_fit_dependency`

## Fit-Aware Measured Pack Rebuild

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_build_fit_aware_pack_from_existing_pack.py`
- Result: pass
- Notes:
  - Fit-aware rebuild from existing pack validation pass
  - Output candidate metadata includes `path_power_fit_proxy`
  - Source profile parity thresholds preserved

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_fit_aware_pack_from_existing_pack.py --source-pack-root /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run1/packs/pack_xiangyu_2019_04_09_bms1000_v1 --output-pack-root /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_bms1000_run1_scattering_mixed/packs/pack_xiangyu_2019_04_09_bms1000_v1_fitaware --path-power-fit-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_scattering_selected.json --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_bms1000_run1_scattering_mixed/fit_aware_pack_summary.json`
- Result: pass
- Notes:
  - Real pack rebuild completed (`selected_candidate_count=128`, `adc_order=scrt`)
  - Fit-aware proxy path bound to mixed scattering fit

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_measured_replay_plan.py --packs-root /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_bms1000_run1_scattering_mixed/packs --output-plan-json /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_bms1000_run1_scattering_mixed/measured_replay_plan.json && PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_measured_replay_execution.py --plan-json /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_bms1000_run1_scattering_mixed/measured_replay_plan.json --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_bms1000_run1_scattering_mixed/measured_replay_outputs --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_bms1000_run1_scattering_mixed/measured_replay_summary.json --allow-unlocked`
- Result: pass
- Notes:
  - Baseline (`run1`) replay pass/fail: `1/127`
  - Fit-aware replay pass/fail: `12/116` (pass_count `+11`)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/analyze_measured_replay_fit_change_impact.py --plan-json /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_bms1000_run1_scattering_mixed/measured_replay_plan.json --fit-dir /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed --output-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/measured_replay_fit_change_impact_fit_aware_bms1000_run1_2026_02_21.json`
- Result: pass
- Notes:
  - `predicted_noop_all_plans=false`
  - recommendation: `rerun_required_for_impacted_plans`

## Fit-Aware Measured Replay Batch Scaling

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_fit_aware_measured_replay_batch.py`
- Result: pass
- Notes:
  - No-gain stop-gate validation pass (`max_no_gain_attempts=1` synthetic case)
  - Stop reason asserted as `max_no_gain_reached`

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_fit_aware_measured_replay_batch.py --case bms1000_512=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/packs/pack_xiangyu_2019_04_09_bms1000_v1_512 --case bms1000_full897=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run3_full897/packs/pack_xiangyu_2019_04_09_bms1000_v1_full897 --case cms1000_128=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/packs/pack_xiangyu_2019_04_09_cms1000_v1_128 --fit-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_scattering_selected.json --fit-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_reflection_selected.json --max-no-gain-attempts 2 --allow-unlocked --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_target_batch_v1 --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_measured_replay_batch_xiangyu_targets_2026_02_21.json`
- Result: pass
- Notes:
  - `case_count=3`, `improved_case_count=3`
  - Best attempt in all cases was scattering mixed fit
  - Stop-gate remained armed but not triggered (`stop_reason=fit_list_exhausted` for all cases)

## Fit-Aware Replay Saturation Gate

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_fit_aware_replay_saturation.py`
- Result: pass
- Notes:
  - Saturation analyzer classification pass (saturated vs normal synthetic cases)
  - Gate fail/pass boundary check pass via `max_allowed_saturated_cases` sweep (`0 -> fail`, `1 -> pass`)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/analyze_fit_aware_replay_saturation.py --batch-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_measured_replay_batch_xiangyu_targets_2026_02_21.json --output-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_replay_saturation_gate_xiangyu_targets_2026_02_21.json --max-allowed-saturated-cases 0`
- Result: pass
- Notes:
  - `case_count=3`, `saturated_case_count=2`
  - gate failed with recommendation `proxy_strength_review_required`
  - saturated cases: `bms1000_512`, `bms1000_full897`

## Fit-Aware Batch Baseline Rerun Correction

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_fit_proxy_policy_cap.py`
- Result: pass
- Notes:
  - Proxy policy cap validation pass (`range/azimuth exponent caps`, `weight clip`)
  - Range weight span reduction check pass

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_measured_replay_plan.py --packs-root /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/packs --output-plan-json /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/measured_replay_plan_rerun_2026_02_21.json && PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_measured_replay_execution.py --plan-json /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/measured_replay_plan_rerun_2026_02_21.json --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/measured_replay_outputs_rerun_2026_02_21 --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/measured_replay_summary_rerun_2026_02_21.json --allow-unlocked`
- Result: pass
- Notes:
  - Current-code rerun baseline for `bms1000_512` is `512/0` (pass_rate `1.0`)
  - Confirms historical baseline report (`1/511`) was stale/incomparable

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_fit_aware_measured_replay_batch.py --baseline-mode rerun --case bms1000_512=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/packs/pack_xiangyu_2019_04_09_bms1000_v1_512 --case bms1000_full897=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run3_full897/packs/pack_xiangyu_2019_04_09_bms1000_v1_full897 --case cms1000_128=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/packs/pack_xiangyu_2019_04_09_cms1000_v1_128 --fit-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_scattering_selected.json --fit-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_reflection_selected.json --max-no-gain-attempts 2 --allow-unlocked --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_target_batch_v2_rerun_baseline --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_measured_replay_batch_xiangyu_targets_rerun_baseline_2026_02_21.json`
- Result: pass
- Notes:
  - `case_count=3`, `improved_case_count=0`
  - all cases hit `max_no_gain_reached` after 2 attempts
  - fit-aware attempts degraded vs rerun baseline on all target plans

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/analyze_fit_aware_replay_saturation.py --batch-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_measured_replay_batch_xiangyu_targets_rerun_baseline_2026_02_21.json --output-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_replay_saturation_gate_xiangyu_targets_rerun_baseline_2026_02_21.json --max-allowed-saturated-cases 0`
- Result: pass
- Notes:
  - `saturated_case_count=0`, `gate_failed=false`
  - recommendation: `proxy_strength_within_expected_range`

## Fit-Aware Replay Policy Gate

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_fit_aware_replay_policy_gate.py`
- Result: pass
- Notes:
  - Synthetic non-degrading improved batch accepted (`accept_fit_lock`)
  - Synthetic degradation-only batch rejected (`reject_fit_lock_due_to_degradation`)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/evaluate_fit_aware_replay_policy_gate.py --batch-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_measured_replay_batch_xiangyu_targets_rerun_baseline_2026_02_21.json --output-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_replay_policy_gate_xiangyu_rerun_baseline_2026_02_21.json --require-non-degradation-all-cases --min-improved-cases 1`
- Result: pass
- Notes:
  - `case_count=3`, `degrade_only_case_count=3`, `improved_case_count=0`
  - gate failed with recommendation `reject_fit_lock_due_to_degradation`

## Fit-Lock Policy Selection Fallback

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_select_measured_replay_fit_lock_by_policy.py`
- Result: pass
- Notes:
  - Eligible fit selected in positive synthetic case
  - Fallback selection (`baseline_no_fit`) triggered when policy cannot be satisfied

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/select_measured_replay_fit_lock_by_policy.py --batch-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_measured_replay_batch_xiangyu_targets_rerun_baseline_2026_02_21.json --output-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/measured_replay_fit_lock_policy_selection_xiangyu_rerun_baseline_2026_02_21.json --min-improved-cases 1 --require-full-case-coverage`
- Result: pass
- Notes:
  - fit candidates evaluated: `2`, eligible: `0`
  - final selection mode: `baseline_no_fit`
  - recommendation: `fallback_to_baseline_no_fit`

## Fit-Lock Search Headroom Gate

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_measured_replay_fit_lock_search.py`
- Result: pass
- Notes:
  - zero-headroom baseline synthetic case short-circuited before batch run
  - fallback selection emitted as `baseline_no_fit`

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_measured_replay_fit_lock_search.py --baseline-mode rerun --case bms1000_512=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/packs/pack_xiangyu_2019_04_09_bms1000_v1_512 --case bms1000_full897=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run3_full897/packs/pack_xiangyu_2019_04_09_bms1000_v1_full897 --case cms1000_128=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/packs/pack_xiangyu_2019_04_09_cms1000_v1_128 --fit-dir /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits --fit-dir /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_cross_family --fit-dir /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed --min-improved-cases 1 --require-full-case-coverage --allow-unlocked --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_fit_lock_search_v1 --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/measured_replay_fit_lock_search_xiangyu_rerun_baseline_2026_02_21.json`
- Result: pass
- Notes:
  - fit candidates discovered: `6`
  - `cases_with_improvement_headroom=0` (all rerun baselines `pass_rate=1.0`)
  - short-circuit executed and final selection set to `baseline_no_fit`

## Saturated-Baseline Drift Objective

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_select_measured_replay_fit_lock_by_drift_objective.py`
- Result: pass
- Notes:
  - lower-drift fit selected in synthetic non-degrading case
  - strict drift bound forces fallback `baseline_no_fit`

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/select_measured_replay_fit_lock_by_drift_objective.py --batch-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_measured_replay_batch_xiangyu_targets_rerun_baseline_2026_02_21.json --output-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/measured_replay_fit_lock_drift_selection_xiangyu_rerun_baseline_2026_02_21.json --require-full-case-coverage`
- Result: pass
- Notes:
  - selected fit: `path_power_fit_reflection_selected.json`
  - recommendation: `exploratory_fit_candidate_selected_by_drift`
  - reflection score (`139.3903`) < scattering score (`141.3810`)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_measured_replay_fit_lock_search.py --baseline-mode provided --objective-mode drift --case bms1000_512=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/packs/pack_xiangyu_2019_04_09_bms1000_v1_512::/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_target_batch_v2_rerun_baseline/case_00_bms1000_512/baseline_current/measured_replay_outputs/pack_xiangyu_2019_04_09_bms1000_v1_512/replay_report.json --fit-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_scattering_selected.json --fit-json /Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_reflection_selected.json --allow-unlocked --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_fit_lock_search_drift_probe_v1 --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/measured_replay_fit_lock_search_drift_probe_bms512_2026_02_21.json`
- Result: pass
- Notes:
  - objective effective mode: `drift`
  - no short-circuit despite zero improvement headroom
  - policy gate fail retained; drift selector still emitted exploratory candidate ranking

## Constrained Refit Drift Search

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_constrained_refit_drift_search.py`
- Result: pass
- Notes:
  - synthetic pack + provided baseline end-to-end constrained loop pass
  - emitted row contains drift-objective selection and valid artifact paths
  - fixed default `flat` preset to use valid positive range exponents

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_constrained_refit_drift_search.py --baseline-mode provided --case bms1000_512=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/packs/pack_xiangyu_2019_04_09_bms1000_v1_512::/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_target_batch_v2_rerun_baseline/case_00_bms1000_512/baseline_current/measured_replay_outputs/pack_xiangyu_2019_04_09_bms1000_v1_512/replay_report.json --csv-case bms1000_512=/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/experiment_matrix/csv_512/bms1000_path_power_samples_512.csv --allow-unlocked --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_constrained_refit_bms512_all_presets_v1 --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/constrained_refit_drift_search_xiangyu_bms512_all_presets_2026_02_21.json`
- Result: pass
- Notes:
  - preset count: `3` (`flat`, `balanced`, `steep`)
  - best preset: `flat`
  - recommendations by preset:
    - `flat`: `adopt_selected_fit_by_drift_objective` (score `0.0512`)
    - `balanced`: `exploratory_fit_candidate_selected_by_drift` (score `0.3435`)
    - `steep`: `exploratory_fit_candidate_selected_by_drift` (score `132.6327`)

## Constrained Refit Consistency Gate

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_evaluate_constrained_refit_consistency_gate.py`
- Result: pass
- Notes:
  - success path selects lowest-score adopt preset
  - strict metric drift threshold triggers deterministic fallback `baseline_no_fit`

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_constrained_refit_drift_search.py --baseline-mode provided --case bms1000_512=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/packs/pack_xiangyu_2019_04_09_bms1000_v1_512::/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_target_batch_v2_rerun_baseline/case_00_bms1000_512/baseline_current/measured_replay_outputs/pack_xiangyu_2019_04_09_bms1000_v1_512/replay_report.json --case bms1000_full897=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run3_full897/packs/pack_xiangyu_2019_04_09_bms1000_v1_full897::/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_target_batch_v2_rerun_baseline/case_01_bms1000_full897/baseline_current/measured_replay_outputs/pack_xiangyu_2019_04_09_bms1000_v1_full897/replay_report.json --case cms1000_128=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/packs/pack_xiangyu_2019_04_09_cms1000_v1_128::/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_target_batch_v2_rerun_baseline/case_02_cms1000_128/baseline_current/measured_replay_outputs/pack_xiangyu_2019_04_09_cms1000_v1_128/replay_report.json --csv-case bms1000=/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/experiment_matrix/csv_512/bms1000_path_power_samples_512.csv --csv-case cms1000=/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/experiment_matrix/csv_128/cms1000_path_power_samples_128.csv --allow-unlocked --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_constrained_refit_targets_all_presets_v1 --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/constrained_refit_drift_search_xiangyu_targets_all_presets_2026_02_21.json`
- Result: pass
- Notes:
  - preset count: `3`, case count: `3`, fit candidates per preset: `4`
  - search-best preset by score: `flat` (`42.7271`)
  - all presets remained exploratory (`exploratory_fit_candidate_selected_by_drift`)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/evaluate_constrained_refit_consistency_gate.py --constrained-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/constrained_refit_drift_search_xiangyu_targets_all_presets_2026_02_21.json --output-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/constrained_refit_consistency_gate_xiangyu_targets_2026_02_21.json`
- Result: pass
- Notes:
  - `eligible_preset_count=0`, `gate_failed=true`
  - final decision: `fallback_to_baseline_no_fit`
  - rejection roots: non-zero degradation terms across all presets

## Targeted Flat-Refine Search (M10.30)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_constrained_refit_drift_search.py`
- Result: pass
- Notes:
  - constrained search validation still passes with new pass-through options
  - argument wiring verified for `max-no-gain-attempts`, drift limits, fit-proxy caps

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_constrained_refit_drift_search.py --baseline-mode provided --case bms1000_512=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/packs/pack_xiangyu_2019_04_09_bms1000_v1_512::/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_target_batch_v2_rerun_baseline/case_00_bms1000_512/baseline_current/measured_replay_outputs/pack_xiangyu_2019_04_09_bms1000_v1_512/replay_report.json --case bms1000_full897=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run3_full897/packs/pack_xiangyu_2019_04_09_bms1000_v1_full897::/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_target_batch_v2_rerun_baseline/case_01_bms1000_full897/baseline_current/measured_replay_outputs/pack_xiangyu_2019_04_09_bms1000_v1_full897/replay_report.json --case cms1000_128=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/packs/pack_xiangyu_2019_04_09_cms1000_v1_128::/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_target_batch_v2_rerun_baseline/case_02_cms1000_128/baseline_current/measured_replay_outputs/pack_xiangyu_2019_04_09_cms1000_v1_128/replay_report.json --csv-case bms1000=/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/experiment_matrix/csv_512/bms1000_path_power_samples_512.csv --csv-case cms1000=/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/experiment_matrix/csv_128/cms1000_path_power_samples_128.csv --preset flat_fine_a --preset flat_fine_b --preset flat_fine_c --max-no-gain-attempts 8 --require-full-case-coverage --drift-max-pass-rate-drop 0.0 --drift-max-pass-count-drop-ratio 0.0 --drift-max-fail-count-increase-ratio 0.0 --drift-max-metric-drift 0.1 --fit-proxy-max-range-exp 1.25 --fit-proxy-max-azimuth-power 1.5 --fit-proxy-min-weight 0.9 --fit-proxy-max-weight 1.1 --allow-unlocked --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_constrained_refit_targets_flat_refine_v2 --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/constrained_refit_drift_search_xiangyu_targets_flat_refine_v2_2026_02_21.json`
- Result: pass
- Notes:
  - preset count: `3`, case count: `3`, fit candidates per preset: `4`
  - all presets returned `selection_mode=baseline_no_fit`
  - no-gain truncation removed vs previous run (full fit-candidate evidence captured)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/evaluate_constrained_refit_consistency_gate.py --constrained-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/constrained_refit_drift_search_xiangyu_targets_flat_refine_v2_2026_02_21.json --output-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/constrained_refit_consistency_gate_xiangyu_targets_flat_refine_v2_2026_02_21.json`
- Result: pass
- Notes:
  - `eligible_preset_count=0`, decision `fallback_to_baseline_no_fit`
  - gate output normalized to JSON-safe nullable diagnostics (no Infinity for missing selected-fit summaries)

## Case-Partitioned Fit-Lock Search (M10.31)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_case_partitioned_fit_lock_search.py`
- Result: pass
- Notes:
  - global baseline fallback path validated
  - family fallback searches executed and final strategy contract verified

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_case_partitioned_fit_lock_search.py --baseline-mode provided --objective-mode drift --global-search-summary-json /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_constrained_refit_targets_flat_refine_v2/preset_00_flat_fine_a/fit_lock_search_summary.json --case bms1000_512=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/packs/pack_xiangyu_2019_04_09_bms1000_v1_512::/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_target_batch_v2_rerun_baseline/case_00_bms1000_512/baseline_current/measured_replay_outputs/pack_xiangyu_2019_04_09_bms1000_v1_512/replay_report.json --case bms1000_full897=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run3_full897/packs/pack_xiangyu_2019_04_09_bms1000_v1_full897::/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_target_batch_v2_rerun_baseline/case_01_bms1000_full897/baseline_current/measured_replay_outputs/pack_xiangyu_2019_04_09_bms1000_v1_full897/replay_report.json --case cms1000_128=/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/packs/pack_xiangyu_2019_04_09_cms1000_v1_128::/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_target_batch_v2_rerun_baseline/case_02_cms1000_128/baseline_current/measured_replay_outputs/pack_xiangyu_2019_04_09_cms1000_v1_128/replay_report.json --case-family bms1000_512=bms1000 --case-family bms1000_full897=bms1000 --case-family cms1000_128=cms1000 --fit-dir /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_constrained_refit_targets_flat_refine_v2/preset_00_flat_fine_a/fit_batch/fits --fit-glob '*.json' --max-no-gain-attempts 8 --require-full-case-coverage --drift-max-pass-rate-drop 0.0 --drift-max-pass-count-drop-ratio 0.0 --drift-max-fail-count-increase-ratio 0.0 --drift-max-metric-drift 0.1 --fit-proxy-max-range-exp 1.25 --fit-proxy-max-azimuth-power 1.5 --fit-proxy-min-weight 0.9 --fit-proxy-max-weight 1.1 --allow-unlocked --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_case_partitioned_fit_lock_v1 --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/case_partitioned_fit_lock_xiangyu_targets_flat_refine_v1_2026_02_21.json`
- Result: pass
- Notes:
  - reused global summary (`reused_global_search_summary=true`)
  - global remained `baseline_no_fit`
  - family results:
    - `bms1000`: `fit` (`adopt_selected_fit_by_drift_objective`, `bms1000_reflection.json`)
    - `cms1000`: `baseline_no_fit`
  - final strategy: `mixed_family_partitioned_lock`

## Object Scene to Radar Map (M11.0)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_to_radar_map.py`
- Result: pass
- Notes:
  - object-scene JSON contract wired (`backend + radar + map_config`)
  - artifacts generated: `path_list.json`, `adc_cube.npz`, `radar_map.npz`, `hybrid_estimation.npz`
  - map shape checks pass (`fx_dop_win=(64,128)`, `fx_ang=(32,128)`)

## Case-Partitioned Lock Manifest Replay (M11.1)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_case_partitioned_lock_manifest_replay.py`
- Result: pass
- Notes:
  - family-level fit selection is materialized to case-level resolved pack roots
  - mixed mode validated (`fit_aware_rebuilt_pack` + `baseline_source_pack`)
  - measured replay verification artifacts emitted (`case_level_lock_manifest.json`, measured replay plan/summary)
