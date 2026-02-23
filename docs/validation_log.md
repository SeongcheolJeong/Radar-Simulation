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

## Native Scene Path Generator Stub (M11.2)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_to_radar_map.py`
- Result: pass
- Notes:
  - regression check: `hybrid_frames` backend path remains valid after backend router refactor

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_analytic_backend.py`
- Result: pass
- Notes:
  - new non-frame backend `analytic_targets` emits canonical artifacts
  - map outputs validated (`fx_dop_win`, `fx_ang`) with expected shapes

## Propagation Schema Expansion (M11.3)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_frame_adapter.py`
- Result: pass
- Notes:
  - hybrid frame adapter remains stable with extended Path metadata fields

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_to_radar_map.py`
- Result: pass
- Notes:
  - `path_list.json` includes metadata fields (`path_id`, `material_tag`, `reflection_order`) for `hybrid_frames`

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_analytic_backend.py`
- Result: pass
- Notes:
  - `analytic_targets` backend path metadata emission validated

## Multi-Backend Parity Harness (M11.4)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_backend_parity.py`
- Result: pass
- Notes:
  - harness executes both scene backends (`hybrid_frames`, `analytic_targets`)
  - parity summary JSON emitted with metrics/failures payload

## Mesh/Material Backend Candidate (M12.0)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_mesh_material_backend.py`
- Result: pass
- Notes:
  - new backend `mesh_material_stub` emits canonical artifacts from object/material scene inputs
  - path metadata includes `path_id/material_tag/reflection_order` for object-level traceability

## Mesh Scene Import Bridge (M12.1)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mesh_scene_import_bridge.py`
- Result: pass
- Notes:
  - external asset manifest is normalized into `mesh_material_stub` scene JSON
  - bridge output runs through scene pipeline and emits canonical artifacts

## Sidecar Asset Parser (M12.2)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sidecar_asset_parser.py`
- Result: pass
- Notes:
  - parser normalizes `glTF/OBJ` sidecar mesh references into `asset_manifest.json`
  - parser output is compatible with bridge and downstream scene pipeline

## Sidecar Schema Lock + Strict Gate (M12.3)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sidecar_asset_parser.py`
- Result: pass
- Notes:
  - strict-mode parser gate validated (`unknown top-level key -> reject`)
  - schema lock metadata validated (`schema_profile=v1`, `schema_version=1`, `strict_mode=true`)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mesh_scene_import_bridge.py`
- Result: pass
- Notes:
  - downstream bridge regression check pass after parser strict-gate integration

## Sidecar Strict/Non-Strict Matrix + Bridge E2E (M12.4)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sidecar_schema_compat_matrix.py`
- Result: pass
- Notes:
  - strict mode rejects unknown sidecar fields
  - non-strict mode accepts unknown fields and records parser diagnostics (`unknown_top_level_keys`, `unknown_object_keys`)
  - non-strict manifest remains bridge-compatible and emits canonical scene artifacts

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sidecar_asset_parser.py`
- Result: pass
- Notes:
  - strict schema-lock regression remains stable after diagnostics extension

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mesh_scene_import_bridge.py`
- Result: pass
- Notes:
  - bridge regression remains stable after sidecar diagnostics extension

## Public Scene Asset Onboarding (M12.5)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_public_scene_asset_onboarding.py`
- Result: pass
- Notes:
  - onboarding runner validated with local source-path fixture
  - sidecar -> manifest -> scene -> canonical outputs path validated offline

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_public_scene_asset_onboarding.py --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/scene_asset_onboarding/khronos_box_v1 --asset-url https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Box/glTF-Binary/Box.glb --asset-relative-path assets/Box.glb --scene-id khronos_box_v1 --object-layout-preset single --strict --summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/public_scene_asset_onboarding_khronos_box_v1_2026_02_21.json`
- Result: pass
- Notes:
  - public sample download + onboarding run completed
  - summary locked with `asset_sha256` and output artifact paths

## Public Multi-Object Fixture Bundle (M12.6)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_public_scene_asset_onboarding.py`
- Result: pass
- Notes:
  - single-object onboarding validator still passes after replay-bundle manifest extension

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_public_multi_object_fixture_bundle.py`
- Result: pass
- Notes:
  - triple-lane multi-object preset emits deterministic artifact hash set across repeated runs

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_public_scene_asset_onboarding.py --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/scene_asset_onboarding/khronos_box_triple_lane_v1 --asset-url https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Box/glTF-Binary/Box.glb --asset-relative-path assets/Box.glb --scene-id khronos_box_triple_lane_v1 --object-layout-preset triple_lane --strict --summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/public_scene_asset_onboarding_khronos_box_triple_lane_v1_2026_02_21.json`
- Result: pass
- Notes:
  - real public sample multi-object run completed
  - replay bundle manifest generated with artifact hashes

## Public OBJ Mixed-Format Matrix (M12.7)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_public_mixed_format_fixture_matrix.py`
- Result: pass
- Notes:
  - local glTF/OBJ fixture matrix validates parser mesh-format mapping parity
  - both formats produce canonical outputs

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_public_scene_asset_onboarding.py --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/scene_asset_onboarding/walthead_obj_v1 --asset-url https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/obj/walt/WaltHead.obj --asset-relative-path assets/WaltHead.obj --scene-id walthead_obj_v1 --object-layout-preset single --strict --summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/public_scene_asset_onboarding_walthead_obj_v1_2026_02_21.json`
- Result: pass
- Notes:
  - real public OBJ onboarding run completed
  - summary locked with OBJ asset hash and output artifact paths

## Mesh Geometry Proxy Extractor (M13.0)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mesh_geometry_proxy_extractor.py`
- Result: pass
- Notes:
  - missing geometry fields are auto-filled from mesh assets (`OBJ`, `glTF`)
  - parser metadata captures auto-geometry diagnostics
  - bridge + scene pipeline compatibility confirmed

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sidecar_asset_parser.py`
- Result: pass
- Notes:
  - sidecar parser regression remains stable after auto-geometry integration

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sidecar_schema_compat_matrix.py`
- Result: pass
- Notes:
  - strict/non-strict schema lock and diagnostics remain stable after geometry integration

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mesh_scene_import_bridge.py`
- Result: pass
- Notes:
  - bridge regression remains stable with geometry auto-fill metadata expansion

## Sionna RT Backend Adapter (M13.1)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_sionna_backend.py`
- Result: pass
- Notes:
  - `sionna_rt` backend emits canonical outputs from exported path payload JSON
  - path metadata forwarding validated (`path_id`, `material_tag`, `reflection_order`)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_backend_parity_sionna_rt.py`
- Result: pass
- Notes:
  - parity harness pass confirmed on matched `analytic_targets` vs `sionna_rt` synthetic pair

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_backend_parity.py`
- Result: pass
- Notes:
  - existing parity harness regression remains stable after `sionna_rt` backend routing addition

## PO-SBR Backend Adapter Candidate (M13.2)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_po_sbr_backend.py`
- Result: pass
- Notes:
  - `po_sbr_rt` backend emits canonical outputs from PO-SBR-style path payload JSON
  - path metadata forwarding validated (`path_id`, `material_tag`, `reflection_order`)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_backend_parity_po_sbr_rt.py`
- Result: pass
- Notes:
  - parity harness pass confirmed on matched `analytic_targets` vs `po_sbr_rt` synthetic pair

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_sionna_backend.py`
- Result: pass
- Notes:
  - `sionna_rt` regression remains stable after PO-SBR backend routing addition

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_backend_parity.py`
- Result: pass
- Notes:
  - existing parity harness regression remains stable with `po_sbr_rt` addition

## RadarSimPy Periodic Parity Lock (M13.3)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_radarsimpy_periodic_parity_lock.py`
- Result: pass
- Notes:
  - periodic lock manifest runner validated on pass-only and mixed(pass+fail) cases
  - threshold gate and runtime diagnostics (`radarsimpy available/unavailable`) validated

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_po_sbr_backend.py`
- Result: pass
- Notes:
  - `po_sbr_rt` regression remains stable after periodic lock module integration

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_sionna_backend.py`
- Result: pass
- Notes:
  - `sionna_rt` regression remains stable after periodic lock module integration

## Scene Runtime Coupling Feasibility (M14.0)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_backend_runtime_coupling.py`
- Result: pass
- Notes:
  - runtime provider execution path validated for `sionna_rt` and `po_sbr_rt` without pre-exported path JSON
  - runtime failure policy validated (`error`, `use_static`) including missing-module fallback
  - `runtime_resolution` metadata emitted for runtime/debug triage

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_sionna_backend.py`
- Result: pass
- Notes:
  - existing static payload regression remains stable after runtime-coupling integration

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_po_sbr_backend.py`
- Result: pass
- Notes:
  - existing static payload regression remains stable after runtime-coupling integration

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_backend_parity_sionna_rt.py`
- Result: pass
- Notes:
  - parity harness remains stable after runtime-coupling integration

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_backend_parity_po_sbr_rt.py`
- Result: pass
- Notes:
  - parity harness remains stable after runtime-coupling integration

## Scene Runtime Environment Probe (M14.1)

- Date: 2026-02-21
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_env_probe.py`
- Result: pass
- Notes:
  - runtime readiness summary schema validated (`python`, `module_report`, `runtime_report`)
  - `ready` rule consistency validated (`repo_found && missing_required_modules == 0`)
  - runtime tracks covered (`sionna_rt_mitsuba_runtime`, `sionna_runtime`, `po_sbr_runtime`)

## Scene Runtime Mitsuba Pilot (M14.2)

- Date: 2026-02-22
- Command: `PYTHONPATH=src /Users/seongcheoljeong/Documents/Codex_test/.venv-sionna311/bin/python /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_mitsuba_pilot.py`
- Result: pass
- Notes:
  - real runtime provider path validated with Mitsuba ray intersection
  - canonical artifacts emitted without pre-exported path JSON
  - runtime metadata confirms `runtime_resolution.mode=runtime_provider`

- Date: 2026-02-22
- Command: `PYTHONPATH=src /Users/seongcheoljeong/Documents/Codex_test/.venv-sionna311/bin/python /Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_env_probe.py --workspace-root /Users/seongcheoljeong/Documents/Codex_test --output-summary-json /tmp/scene_runtime_env_probe_summary_m14_2.json`
- Result: pass
- Notes:
  - readiness gate confirms `sionna_rt_mitsuba_runtime_ready=true`
  - `sionna_runtime` and `po_sbr_runtime` remain blocked on missing dependencies

- Date: 2026-02-22
- Command: `PYTHONPATH=src /Users/seongcheoljeong/Documents/Codex_test/.venv-sionna311/bin/python /Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_mitsuba_pilot.py --output-root /Users/seongcheoljeong/Documents/Codex_test/data/runtime_pilot/mitsuba_runtime_pilot_v1 --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_mitsuba_pilot_v1_2026_02_22.json --n-chirps 8 --samples-per-chirp 1024 --target-range-m 25.0 --target-radius-m 0.5`
- Result: pass
- Notes:
  - first real runtime scene pilot executed and report archived

## Runtime Blocker Gate + Sionna PHY Sanity (M14.3)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_env_probe.py`
- Result: pass
- Notes:
  - probe expanded with blocker/status/platform/NVIDIA diagnostics
  - runtime tracks covered: `sionna_rt_mitsuba_runtime`, `sionna_runtime`, `sionna_rt_full_runtime`, `po_sbr_runtime`

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_blocker_report.py`
- Result: pass
- Notes:
  - blocker report emits deterministic `ready_count`, `blocked_count`, and `next_recommended_runtime`
  - blocked tracks include actionable recommendations

- Date: 2026-02-22
- Command: `PYTHONPATH=src /Users/seongcheoljeong/Documents/Codex_test/.venv-sionna311/bin/python /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sionna_phy_runtime_minimal.py`
- Result: pass
- Notes:
  - `sionna 1.2.1` + `tensorflow 2.20.0` runtime sanity confirmed (`tf matmul`, `ebnodb2no`)

- Date: 2026-02-22
- Command: `PYTHONPATH=src /Users/seongcheoljeong/Documents/Codex_test/.venv-sionna311/bin/python /Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_env_probe.py --workspace-root /Users/seongcheoljeong/Documents/Codex_test --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/runtime_probe_m14_3_2026_02_22.json`
- Result: pass
- Notes:
  - `sionna_runtime` and `sionna_rt_mitsuba_runtime` are ready
  - `sionna_rt_full_runtime` blocked on `sionna.rt` import (LLVM backend)
  - `po_sbr_runtime` blocked on missing modules + unsupported platform + missing NVIDIA runtime

- Date: 2026-02-22
- Command: `PYTHONPATH=src /Users/seongcheoljeong/Documents/Codex_test/.venv-sionna311/bin/python /Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_blocker_report.py --probe-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/runtime_probe_m14_3_2026_02_22.json --output-report-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/runtime_blocker_report_m14_3_2026_02_22.json`
- Result: pass
- Notes:
  - blocker report archived with next recommended runtime selection

## Sionna RT LLVM Probe (M14.4)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_sionna_rt_llvm_probe.py`
- Result: pass
- Notes:
  - LLVM probe summary schema validated (`success`, `working_libllvm_path`, per-probe diagnostics)

- Date: 2026-02-22
- Command: `PYTHONPATH=src /Users/seongcheoljeong/Documents/Codex_test/.venv-sionna311/bin/python /Users/seongcheoljeong/Documents/Codex_test/scripts/run_sionna_rt_llvm_probe.py --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/sionna_rt_llvm_probe_m14_4_2026_02_22.json`
- Result: pass
- Notes:
  - probe executed on baseline + 17 candidates (`probe_count=18`)
  - host remains blocked (`success=false`, `working_libllvm_path=null`)
  - blockers observed:
    - llvmlite candidate API mismatch
    - Xcode SDK `libLLVM` candidates are non-macOS target binaries

## Sionna RT Full Runtime Enablement (M14.5)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_env_probe.py`
- Result: pass
- Notes:
  - env probe schema remains stable after `--drjit-libllvm-path` override support
  - `applied_overrides` field added for deterministic runtime-trace metadata

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_blocker_report.py`
- Result: pass
- Notes:
  - blocker report remains deterministic after runtime priority update

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_sionna_rt_llvm_probe.py`
- Result: pass
- Notes:
  - LLVM probe remains schema-stable with macOS-default candidate filtering

- Date: 2026-02-22
- Command: `DRJIT_LIBLLVM_PATH=/Users/seongcheoljeong/Documents/Codex_test/external/runtime/llvm-21.1.6/homebrew17-lib/lib/libLLVM.dylib PYTHONPATH=src /Users/seongcheoljeong/Documents/Codex_test/.venv-sionna311/bin/python -c "import importlib, sionna; importlib.import_module('sionna.rt')"`
- Result: pass
- Notes:
  - direct `sionna.rt` import succeeded on target host (`rc=0`)

- Date: 2026-02-22
- Command: `PYTHONPATH=src /Users/seongcheoljeong/Documents/Codex_test/.venv-sionna311/bin/python /Users/seongcheoljeong/Documents/Codex_test/scripts/run_sionna_rt_llvm_probe.py --extra-candidate /Users/seongcheoljeong/Documents/Codex_test/external/runtime/llvm-21.1.6/homebrew17-lib/lib/libLLVM.dylib --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/sionna_rt_llvm_probe_m14_5_2026_02_22.json`
- Result: pass
- Notes:
  - probe succeeded (`success=true`, `working_libllvm_path` set)
  - probe count reduced (`probe_count=3`) by default macOS-only candidate filtering

- Date: 2026-02-22
- Command: `PYTHONPATH=src /Users/seongcheoljeong/Documents/Codex_test/.venv-sionna311/bin/python /Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_env_probe.py --workspace-root /Users/seongcheoljeong/Documents/Codex_test --drjit-libllvm-path /Users/seongcheoljeong/Documents/Codex_test/external/runtime/llvm-21.1.6/homebrew17-lib/lib/libLLVM.dylib --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/runtime_probe_m14_5_2026_02_22.json`
- Result: pass
- Notes:
  - `sionna_rt_full_runtime_ready=true` with zero blockers
  - `po_sbr_runtime` remains blocked on Darwin+NVIDIA/module constraints

- Date: 2026-02-22
- Command: `PYTHONPATH=src /Users/seongcheoljeong/Documents/Codex_test/.venv-sionna311/bin/python /Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_blocker_report.py --probe-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/runtime_probe_m14_5_2026_02_22.json --output-report-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/runtime_blocker_report_m14_5_2026_02_22.json`
- Result: pass
- Notes:
  - blocker report now recommends `next_recommended_runtime=sionna_rt_full_runtime`

## PO-SBR Runtime Pilot (M14.6)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_po_sbr_runtime_provider_stubbed.py`
- Result: pass
- Notes:
  - PO-SBR runtime provider output contract validated via stubbed solver (`paths_by_chirp`, delay/doppler/path_id mapping)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_runtime_po_sbr_provider_integration_stubbed.py`
- Result: pass
- Notes:
  - `scene_pipeline -> runtime_provider(po_sbr_rt_provider) -> canonical outputs` end-to-end path validated with stubbed PO solver
  - `runtime_resolution.mode=runtime_provider` and provider spec trace validated

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_po_sbr_pilot.py`
- Result: pass
- Notes:
  - pilot summary contract validated for both deterministic states (`blocked|executed`)
  - blocked branch validates actionable blocker reasons and Linux rerun command

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_validate_scene_runtime_po_sbr_executed_report.py`
- Result: pass
- Notes:
  - strict executed-report validator contract validated with synthetic executed summary
  - hard gate now available for Linux strict completion evidence

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_m14_6_closure_readiness.py`
- Result: pass
- Notes:
  - closure readiness checker schema validated
  - missing Linux executed report path is deterministically surfaced

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_finalize_m14_6_from_linux_report.py`
- Result: pass
- Notes:
  - finalize helper not-ready behavior validated (`exit code 2`)
  - readiness JSON is still emitted with `linux_executed_report_missing`

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_po_sbr_pilot.py --output-root /Users/seongcheoljeong/Documents/Codex_test/data/runtime_pilot/po_sbr_runtime_pilot_v1 --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_po_sbr_pilot_m14_6_2026_02_22.json --allow-blocked`
- Result: pass
- Notes:
  - current Darwin host is deterministically blocked
  - blockers: `missing_required_modules`, `unsupported_platform:Darwin`, `missing_nvidia_runtime`
  - report archived with Linux strict rerun command hint

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_m14_6_closure_readiness.py --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/m14_6_closure_readiness_2026_02_22.json`
- Result: pass
- Notes:
  - readiness report archived (`ready=false`)
  - only remaining missing item: `linux_executed_report_missing`

- Date: 2026-02-22
- Command: `bash -n /Users/seongcheoljeong/Documents/Codex_test/scripts/bootstrap_po_sbr_linux_env.sh`
- Result: pass
- Notes:
  - Linux PO-SBR environment bootstrap script syntax validated

- Date: 2026-02-22
- Command: `bash -n /Users/seongcheoljeong/Documents/Codex_test/scripts/run_m14_6_remote_linux_over_ssh.sh`
- Result: pass
- Notes:
  - macOS->Linux SSH orchestration script syntax validated

## Web E2E Orchestrator API (M15.0)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - phase-0 API endpoints validated (`/health`, `/api/profiles`, `/api/runs`, `/api/runs/{id}`, `/api/runs/{id}/summary`)
  - sync run creation path validated (`POST /api/runs?async=0`) with analytic scene
  - run summary quicklook contract validated (`n_chirps`, path counts, ADC/RD/RA shapes, top peaks)

## Web E2E Summary v2 + Dashboard API Mode (M15.1/M15.2)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - run summary upgraded to v2 frontend-compatible schema (`scene_json`, `outputs`, `path_summary`, `adc_summary`, `radar_map_summary`)
  - backward-compatible `quicklook` retained and validated
  - output artifact file existence checks validated
  - compare API validated (`POST /api/compare`, `GET /api/comparisons`, `GET /api/comparisons/{id}`)
  - baseline pin/policy endpoints validated (`POST/GET /api/baselines`, `POST /api/compare/policy`, `GET /api/policy-evals`)

- Date: 2026-02-22
- Command: `scripts/run_web_e2e_dashboard_local.sh 8086 8106` + health/dashboard smoke (`curl /health`, `curl /frontend/avx_like_dashboard.html`)
- Result: pass
- Notes:
  - combined launcher starts orchestrator API + static dashboard in one command
  - dashboard HTML served and API health endpoint returns `ok=true`
  - dashboard contains API run/compare controls (`runSceneViaApi`, `compareRunsViaApi`)
  - dashboard contains baseline/policy controls (`pinBaselineViaApi`, `evaluatePolicyViaApi`)

## Web E2E Regression Session API (M15.4)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - regression session API validated (`POST /api/regression-sessions`, `GET /api/regression-sessions`, `GET /api/regression-sessions/{id}`)
  - batch stop-on-first-fail path validated (`requested=2`, `evaluated=1`, `truncated=true`)
  - health payload includes `regression_session_count`

- Date: 2026-02-22
- Command: `scripts/run_web_e2e_dashboard_local.sh 8093 8113` + smoke (`curl /health`, `curl /frontend/avx_like_dashboard.html?summary=docs/reports/frontend_quickstart_v1.json`)
- Result: pass
- Notes:
  - launcher starts API + dashboard and health returns `ok=true`
  - dashboard HTML includes regression controls (`runRegressionSessionViaApi`)
  - summary fetch path handling now normalizes relative repo paths via `normalizeRepoPath(targetRaw)` before `fetch`

## Web E2E Regression Export API (M15.5)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - regression export API validated (`POST /api/regression-exports`, `GET /api/regression-exports`, `GET /api/regression-exports/{id}`)
  - export artifacts validated: `regression_session.json`, `regression_rows.csv`, `regression_summary_index.json`, `regression_package.json`
  - summary index and package schema checks pass (`version`, row count, policy payload inclusion when enabled)
  - health payload includes `regression_export_count`

## Web E2E Regression History Dashboard Wiring (M15.6)

- Date: 2026-02-22
- Command: `scripts/run_web_e2e_dashboard_local.sh 8094 8114` + smoke (`curl /health`, `curl /frontend/avx_like_dashboard.html?summary=docs/reports/frontend_quickstart_v1.json`)
- Result: pass
- Notes:
  - dashboard HTML includes regression history controls (`refreshRegressionHistoryBtn`, `exportRegressionBtn`, `regressionSessionSelect`, `regressionExportSelect`)
  - dashboard JS includes history/export handlers (`refreshRegressionHistoryViaApi`, `exportRegressionSessionViaApi`)
  - API health includes `regression_export_count`

## Web E2E Regression Gate Overview Panel (M15.7)

- Date: 2026-02-22
- Command: `scripts/run_web_e2e_dashboard_local.sh 8094 8114` + smoke (`curl /health`, `curl /frontend/avx_like_dashboard.html?summary=docs/reports/frontend_quickstart_v1.json`)
- Result: pass
- Notes:
  - dashboard HTML includes gate overview elements (`regressionGateBadge`, `gateCueLine`, `gateLatestSessionLine`)
  - dashboard JS includes gate evaluator (`updateRegressionGateOverview`, `setRegressionGateBadge`)
  - history refresh path updates gate overview from latest session/export lists

## Web E2E Regression Policy Tuning Controls (M15.8)

- Date: 2026-02-22
- Command: `scripts/run_web_e2e_dashboard_local.sh 8095 8115` + smoke (`curl /health`, `curl /frontend/avx_like_dashboard.html?summary=docs/reports/frontend_quickstart_v1.json`) + `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - dashboard HTML includes policy-tuning controls (`regressionPolicyPresetSelect`, `requireParityPassCheck`, `stopOnFirstFailCheck`, `maxFailureCountInput`, `rdShapeNmseMaxInput`, `raShapeNmseMaxInput`)
  - dashboard JS includes tuning collector/applier (`collectPolicyTuningConfig`, `applyPolicyPresetToInputs`)
  - compare/policy/regression-session requests include tuned policy/threshold payload fields

## Web E2E Regression Decision Audit Panel (M15.9)

- Date: 2026-02-22
- Command: `scripts/run_web_e2e_dashboard_local.sh 8097 8117` + smoke (`curl /health`, `curl /frontend/avx_like_dashboard.html?summary=docs/reports/frontend_quickstart_v1.json`) + `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - dashboard HTML includes decision-audit elements (`decisionAuditBadge`, `auditRuleHistogram`, `auditHotCandidateLine`)
  - dashboard JS includes audit evaluator (`updateRegressionDecisionAudit`, `setDecisionAuditBadge`)
  - history refresh now joins `policy-evals` with session rows for rule histogram/trend summary

## Web E2E Review Bundle Hook (M15.10)

- Date: 2026-02-22
- Command: `scripts/run_web_e2e_dashboard_local.sh 8098 8118` + smoke (`curl /health`, `curl /frontend/avx_like_dashboard.html?summary=docs/reports/frontend_quickstart_v1.json`) + `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - dashboard HTML includes review-bundle controls (`copyReviewBundleBtn`, `reviewBundleStatus`, `reviewBundlePathBox`)
  - dashboard JS includes bundle hook/copy helpers (`runReviewBundleCopyHook`, `copyTextToClipboard`, `getReviewBundlePathFromExport`)
  - hook path reuses `POST /api/regression-exports` and resolves bundle path from export artifacts

## Web E2E Decision Report Template Export (M15.11)

- Date: 2026-02-22
- Command: `scripts/run_web_e2e_dashboard_local.sh 8099 8119` + smoke (`curl /health`, `curl /frontend/avx_like_dashboard.html?summary=docs/reports/frontend_quickstart_v1.json`) + `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - dashboard HTML includes report-export controls (`exportDecisionReportBtn`, `decisionReportStatus`, `decisionReportFileBox`)
  - dashboard JS includes markdown template exporter (`buildDecisionReportTemplateMarkdown`, `exportDecisionReportTemplate`)
  - export path includes blob-download + best-effort clipboard copy with status updates

## Web E2E Decision Report Failure Evidence (M15.12)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - API baseline/compare/policy/regression/export endpoints remain stable after dashboard report logic extension
  - no regression observed in orchestrator API contract checks

- Date: 2026-02-22
- Command: `rg -n "collectTopFailureEvidenceRows|formatEvidenceValue|Top Failure Evidence \(Auto-Extracted\)|no gate-failure evidence found" /Users/seongcheoljeong/Documents/Codex_test/frontend/avx_like_dashboard.html`
- Result: pass
- Notes:
  - report exporter includes evidence collector + value formatter helpers
  - markdown template includes top-failure evidence section and no-evidence fallback line

## Web E2E Evidence Drill-Down Panel (M15.13)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - API run/compare/policy/regression/export routes remain stable after evidence drill-down UI wiring

- Date: 2026-02-22
- Command: `scripts/run_web_e2e_dashboard_local.sh 8103 8123` + smoke (`curl /health`, `curl /frontend/avx_like_dashboard.html?summary=/docs/reports/frontend_quickstart_v1.json` + token grep)
- Result: pass
- Notes:
  - dashboard HTML includes evidence drill-down controls (`evidenceCandidateSelect`, `evidenceRuleSelect`, `evidencePivotCompareBtn`, `evidenceOpenPolicyEvalBtn`)
  - dashboard JS includes evidence join/render/actions (`collectFocusedSessionFailureRows`, `updateEvidenceDrillDown`, `pivotCompareCandidateFromDrill`, `openEvidencePolicyEvalFromDrill`)
  - history/session refresh path synchronizes gate/audit/evidence state

## Web E2E Graph Contract Validation API (M16.0)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - new graph contract endpoints validated:
    - `GET /api/graph/templates`
    - `POST /api/graph/validate`
  - valid template graph returns `valid=true` and non-empty topological order
  - invalid cycle graph returns `valid=false` with cycle-related error
  - existing API contract regression remains pass after graph endpoint integration

## Web E2E ReactFlow Shell (M16.1)

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8104 8124` + smoke (`curl /health`, `curl /frontend/graph_lab_reactflow.html?api=...` + token grep)
- Result: pass
- Notes:
  - ReactFlow shell page served from `frontend/graph_lab_reactflow.html`
  - page includes graph-template/validation API wiring (`/api/graph/templates`, `/api/graph/validate`)
  - launcher starts API + static server and health returns `ok=true`

## Web E2E Graph Run Bridge API (M16.2)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - graph run API validated:
    - `POST /api/graph/runs?async=0`
    - `GET /api/graph/runs`
    - `GET /api/graph/runs/{graph_run_id}`
    - `GET /api/graph/runs/{graph_run_id}/summary`
  - health now includes `graph_run_count`
  - graph run summary contract validated (`web_e2e_graph_run_summary_v1`, node results, output artifacts)

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8105 8125` + smoke (`curl /health`, `curl /frontend/graph_lab_reactflow.html?api=...` + token grep)
- Result: pass
- Notes:
  - ReactFlow shell includes graph-run execution hook (`Run Graph (API)`)
  - page wires run endpoint and summary retrieval (`/api/graph/runs`, `/api/graph/runs/{id}/summary`)
  - result panel includes graph-run artifact pointers (`graph_run_summary_json`)

## Web E2E Graph Artifact Inspector (M16.3)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - graph run summary contract remains stable with artifact-inspector frontend integration
  - graph run endpoints and summary artifacts remain valid under regression harness

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8106 8126` + smoke (`curl /health`, `curl /frontend/graph_lab_reactflow.html?api=...` + token grep)
- Result: pass
- Notes:
  - Graph Lab includes `Artifact Inspector` section and `Run Graph (API)` action
  - shell includes graph-run endpoint wiring and trace/visual labels (`/api/graph/runs`, `node trace`, `visuals`)
  - artifact inspector path normalization helper added (`normalizeRepoPath`)

## Web E2E Graph Gate Integration (M16.4)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - validator now covers graph-summary baseline path:
    - `POST /api/baselines` with `summary_json=<graph_run_summary_json>`
    - `POST /api/compare/policy` with `baseline_id + candidate_summary_json`
  - backend resolver patch confirmed (`None/null` run-id token handling in summary-first flows)
  - full API regression suite remains pass after gate integration wiring

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8108 8128` + smoke (`curl /health`, `curl /frontend/graph_lab_reactflow.html?api=...` + token grep)
- Result: pass
- Notes:
  - Graph Lab UI includes graph-run gate controls (`Pin Baseline`, `Policy Gate`, `Export Gate Report (.md)`)
  - `Policy Gate Result` panel is present
  - frontend includes baseline/policy API integration tokens (`/api/baselines`, `/api/compare/policy`)

## Web E2E Graph Hardening (M16.5)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - validator now covers cache/cancel/recovery hardening cases:
    - full cache hit (`cache.mode=required`) on repeated graph run
    - partial rerun cache hit from `RadarMap` node (`rerun_from_node_id`)
    - async cancel (`POST /api/graph/runs/{id}/cancel`)
    - retry from canceled run (`POST /api/graph/runs/{id}/retry`)
    - forced execution failure with structured recovery hints and retry-from-failed override
  - 기존 run/compare/baseline/policy/regression/export regression checks remain pass

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8110 8130` + smoke (`curl /frontend/graph_lab_reactflow.html?api=...` token grep)
- Result: pass
- Notes:
  - Graph Lab page contains M16.5 controls/tokens:
    - `Retry Last Run`
    - `Cancel Last Run`
    - `/api/graph/runs/{id}/retry`
    - `/api/graph/runs/{id}/cancel`
    - `cache_hit` run-result field

## Web E2E Graph Async Monitor (M17.0)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - M16.5 backend run semantics remain stable while Graph Lab async monitor client logic was added
  - no regression observed in graph run/cancel/retry/recovery API contract checks

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8111 8131` + smoke (`curl /frontend/graph_lab_reactflow.html?api=...` token grep)
- Result: pass
- Notes:
  - Graph Lab page contains async monitor controls/tokens:
    - `Run Mode`
    - `Auto Poll`
    - `Poll Last Run`
    - `poll_state`
    - `/api/graph/runs?async=...`
    - `/api/graph/runs/{id}/retry?async=...`

## Web E2E Graph Frontend Modularization (M17.1)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - backend graph run/cancel/retry/policy API contract remains stable after frontend module split
  - no regression observed in existing orchestrator regression harness

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8112 8132` + smoke (`curl /frontend/graph_lab_reactflow.html?api=...` + `curl /frontend/graph_lab/app.mjs` token grep)
- Result: pass
- Notes:
  - Graph Lab HTML shell now loads module entry only (`./graph_lab/main.mjs`)
  - app runtime tokens remain present in external module (`Run Mode`, `Auto Poll`, `Poll Last Run`)
  - async/retry/cancel endpoint bindings remain present in moduleized app (`/api/graph/runs?async=...`, `/retry?async=...`, `/cancel`)

## Web E2E Graph Component + API Split (M17.2)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - frontend refactor 이후에도 graph run/cancel/retry/baseline/policy API regression suite pass
  - backend API contract and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8113 8133` + smoke (`curl /frontend/graph_lab_reactflow.html?api=...`, `curl /frontend/graph_lab/app.mjs`, `curl /frontend/graph_lab/api_client.mjs` token grep)
- Result: pass
- Notes:
  - HTML shell still loads module entry (`./graph_lab/main.mjs`)
  - `app.mjs` contains panel composition tokens (`GraphInputsPanel`, `GraphCanvasPanel`, `NodeInspectorPanel`)
  - `app.mjs` run actions route through API client wrappers (`runGraph`, `retryGraphRun`, `cancelGraphRun`)
  - endpoint strings are centralized in `api_client.mjs` (`/api/graph/runs?async=...`, `/retry?async=...`, `/cancel`, `/api/baselines`, `/api/compare/policy`)

## Web E2E Graph Action Hooks Split (M17.3)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - hook refactor 이후에도 graph run/cancel/retry/baseline/policy API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8114 8134` + smoke (`curl /frontend/graph_lab/app.mjs`, `curl /frontend/graph_lab/hooks/use_graph_run_ops.mjs`, `curl /frontend/graph_lab/hooks/use_gate_ops.mjs` token grep)
- Result: pass
- Notes:
  - `app.mjs` now wires hook entry points (`useGraphRunOps`, `useGateOps`)
  - run hook includes existing run-control API paths (`runGraph`, `retryGraphRun`, `cancelGraphRun`, summary poll path)
  - gate hook includes baseline/policy/report actions (`createBaseline`, `evaluatePolicyGate`, report filename prefix `graph_gate_report_`)

## Web E2E Graph Input Model Grouping (M17.4)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - panel binding shape refactor 이후에도 graph run/cancel/retry/baseline/policy API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8115 8135` + smoke (`curl /frontend/graph_lab/app.mjs`, `curl /frontend/graph_lab/panels.mjs` token grep)
- Result: pass
- Notes:
  - `app.mjs` exports grouped panel model (`inputPanelModel`) with section keys (`values`, `templateActions`, `runActions`, `gateActions`)
  - `GraphInputsPanel` now consumes grouped `model` contract (`{ model }` + grouped destructuring)
  - existing operator UI tokens remain present (`Run Mode`, `Auto Poll`, `Poll Last Run`)

## Web E2E Graph Runtime Contract Guard (M17.5)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - contract/guard integration 이후에도 graph run/cancel/retry/baseline/policy API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8116 8136` + smoke (`curl /frontend/graph_lab/contracts.mjs`, `curl /frontend/graph_lab/app.mjs`, `curl /frontend/graph_lab/panels.mjs`, `curl /frontend/graph_lab/hooks/use_graph_run_ops.mjs`, `curl /frontend/graph_lab/hooks/use_gate_ops.mjs` token grep)
- Result: pass
- Notes:
  - contract version/normalizer tokens served (`graph_inputs_panel_model_v1`, `graph_run_ops_options_v1`, `gate_ops_options_v1`)
  - app/panel/hook guard integration tokens confirmed (`normalizeGraphInputsPanelModel`, `normalizeGraphRunOpsOptions`, `normalizeGateOpsOptions`)
  - run/gate operator controls remain wired with existing semantics under guarded model/options path

## Web E2E Graph Contract Diagnostics Surface (M17.6)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - contract diagnostics integration 이후에도 graph run/cancel/retry/baseline/policy API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8117 8137` + smoke (`curl /frontend/graph_lab/panels.mjs`, `curl /frontend/graph_lab/contracts.mjs`, `curl /frontend/graph_lab/app.mjs` token grep)
- Result: pass
- Notes:
  - panel diagnostics controls present (`Contract Guard`, `Refresh Guard`, `Reset Guard`)
  - contract diagnostics API tokens served (`getContractWarningSnapshot`, `resetContractWarnings`, `contract_warning_debug_v1`)
  - app wiring tokens present (`refreshContractWarnings`, `resetContractWarnings`, `contractDebugText`)

## Web E2E Graph Auto Contract Propagation (M17.7)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - frontend auto-propagation changes 이후에도 graph run/cancel/retry/baseline/policy API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8118 8138` + smoke (`curl /health`, `curl /frontend/graph_lab/*.mjs` token grep)
- Result: pass
- Notes:
  - `app.mjs` auto-refresh dependency token confirmed:
    - `[graphRunText, gateResultText, validationText, refreshContractWarnings]`
  - run hook tokens confirmed:
    - `contract_warning_unique`
    - `contract_warning_attempts`
    - `contract_diagnostics:`
  - gate hook tokens confirmed:
    - `contract_warning_unique`
    - `contract_warning_attempts`
  - panel token confirmed:
    - `Contract Diagnostics (Auto)`

## Web E2E Graph Contract Overlay Timeline (M17.8)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - overlay/timeline frontend integration 이후에도 graph run/cancel/retry/baseline/policy API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8119 8139` + smoke (`curl /health`, `curl /frontend/graph_lab*.mjs` token grep)
- Result: pass
- Notes:
  - app overlay/timeline tokens confirmed:
    - `ContractWarningOverlay`
    - `contractOverlayEnabled`
    - `contractTimeline`
    - `onContractDiagnosticsEvent`
  - contract model/options tokens confirmed:
    - `contractOverlayEnabled`
    - `contractTimelineCount`
    - `setContractOverlayEnabled`
    - `clearContractTimeline`
    - `onContractDiagnosticsEvent`
  - panel + inspector tokens confirmed:
    - `Show Overlay`
    - `Clear Timeline`
    - `Contract Timeline`
    - `contract_delta(unique/attempt)`
  - run/gate hook delta/runtime tokens confirmed:
    - `contract_warning_delta_unique`
    - `contract_warning_delta_attempts`
    - `runtime_contract_diagnostics`
  - overlay CSS tokens confirmed:
    - `contract-overlay`
    - `contract-overlay-row`

## Web E2E Graph Contract Timeline Filter + Export (M17.9)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - timeline filter/export + gate-report diagnostics changes 이후에도 graph run/cancel/retry/baseline/policy API regression suite pass
  - async cancel assertion showed one intermittent timing failure on first try; immediate rerun passed (known flaky cancel timing path)

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8120 8140` + smoke (`curl /health`, `curl /frontend/graph_lab*.mjs` token grep)
- Result: pass
- Notes:
  - app export tokens confirmed:
    - `exportContractTimeline`
    - `contract_timeline_export_v1`
    - `onExport`
  - overlay filter/export tokens confirmed:
    - `Export JSON`
    - `source:`
    - `non-zero delta`
    - `showing filtered/total`
    - `contract-overlay-filter`
  - gate report contract diagnostics tokens confirmed:
    - `## Contract Diagnostics`
    - `runtime_contract_diagnostics`
    - `run.delta_unique`
    - `gate.delta_unique`
    - `contract_debug_version`

## Web E2E Graph Contract Compact Pin + Tail Ref (M17.10)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - compact/pin/tail-ref frontend integration 이후에도 graph run/cancel/retry/baseline/policy API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8121 8141` + smoke (`curl /health`, `curl /frontend/graph_lab*.mjs` token grep)
- Result: pass
- Notes:
  - overlay compact/pin/severity tokens confirmed:
    - `Compact: on/off`
    - `run:`
    - `pinnedRunId`
    - `classifyContractSeverity`
    - `contract-sev-badge`
    - `contract-overlay-row-compact`
  - gate timeline-tail report tokens confirmed:
    - `## Contract Timeline Tail`
    - `timeline_export_hint`
    - `tail_event_count`
    - `scoped_event_count`
    - `sev=`
  - gate options + app wiring tokens confirmed:
    - `contractTimeline: readArray(...)`
    - `contractTimeline` pass-through from app

## Web E2E Graph Timeline Jump + Policy Correlation (M17.11/M17.12)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - timeline jump/correlation frontend integration 이후에도 graph run/cancel/retry/baseline/policy API regression suite pass
  - async cancel assertion showed one intermittent timing failure on re-run; immediate rerun passed (known flaky cancel timing path)
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8122 8142` + smoke (`curl /health`, `curl /frontend/graph_lab*.mjs` token grep)
- Result: pass
- Notes:
  - run-jump tokens confirmed:
    - `openGraphRunById`
    - `opening graph run`
    - `graph_run_overlay_open`
    - `opened_from_overlay`
    - `onOpenRun`
    - `Open Run`
  - timeline policy tag tokens confirmed:
    - `Open Gate`
    - `getPolicyCorrelationTag`
    - `getFailureRuleTags`
    - `policy:HOLD#`
    - `policy:ADOPT`
    - `contract-policy-tag`
    - `contract-failure-rule-badge`
  - gate report correlation tokens confirmed:
    - `failure_rules`
    - `failure_count`
    - `| policy=`
    - `## Contract Timeline Tail`

## Web E2E Graph Timeline Gate Deep-Link + Rule Badges (M17.13)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - timeline gate deep-link/rule-badge integration 이후에도 graph run/cancel/retry/baseline/policy API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `scripts/run_graph_lab_local.sh 8123 8143` + smoke (`curl /health`, `curl /frontend/graph_lab*.mjs` token grep)
- Result: pass
- Notes:
  - deep-link tokens confirmed:
    - `Open Run`
    - `Open Gate`
    - `onOpenRun`
    - `onOpenGateEvidence`
    - `openGraphRunById`
  - correlation/rule badge tokens confirmed:
    - `contract-policy-tag`
    - `contract-failure-rule-badge`
    - `getFailureRuleTags`
  - gate note/report tokens confirmed:
    - `policy_eval_id`
    - `recommendation`
    - `failure_rules`
    - `failure_count`
    - `| policy=`

## Web E2E Graph Historical Policy-Eval Fetch (M17.14)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - historical gate-evidence fetch frontend changes 이후에도 graph run/cancel/retry/baseline/policy API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8145/8125)` + token grep (`curl /health`, `curl /frontend/graph_lab/app.mjs`, `curl /frontend/graph_lab/api_client.mjs`, `curl /frontend/graph_lab/hooks/use_gate_ops.mjs`)
- Result: pass
- Notes:
  - app historical fetch tokens confirmed:
    - `getPolicyEval`
    - `listPolicyEvals`
    - `policy_eval_list:run_id+summary_json`
    - `evidence_source: persisted/`
    - `gate evidence unresolved`
  - API client endpoint tokens confirmed:
    - `/api/policy-evals`
    - `/api/policy-evals/{id}`
  - gate note hint tokens confirmed:
    - `candidate_run_id`
    - `candidate_summary_json`

## Web E2E Graph Policy-Eval Filtered Paging + Cache (M17.15)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - policy-eval filtered paging backend addition 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8146/8126)` + endpoint/page assertion + token grep (`curl /api/policy-evals?...`, `curl /frontend/graph_lab/app.mjs`, `curl /frontend/graph_lab/api_client.mjs`)
- Result: pass
- Notes:
  - `/api/policy-evals` page metadata contract confirmed:
    - `page.total_count`
    - `page.returned_count`
    - `page.limit`
    - `page.offset`
    - `page.filtered.candidate_run_id`
    - `page.filtered.baseline_id`
  - frontend cache/scoped-query tokens confirmed:
    - `fetchPolicyEvalListCached`
    - `run_id+baseline_id`
    - `policy_eval_cache_hit_any`
  - API client filtered query tokens confirmed:
    - `candidate_run_id`
    - `baseline_id`
    - `limit`
    - `offset`

## Web E2E Graph Overlay Gate-History Window + Incremental Lookup (M17.16)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass (2nd run)
- Notes:
  - 첫 실행에서 async cancel 타이밍 경합으로 간헐적 assertion 발생, 즉시 재실행 pass (known flaky path)
  - overlay gate-history control/incremental lookup frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8147/8127)` + filtered endpoint assertion + token grep (`curl /api/policy-evals?...`, `curl /frontend/graph_lab/app.mjs`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - filtered endpoint query contract reaffirmed (`limit=64`, `offset=128`)
  - app incremental lookup tokens confirmed:
    - `historyLimit`
    - `pageBudget`
    - `policy_eval_page_budget`
    - `policy_eval_page_count_used`
    - `@page`
  - overlay control/pass-through tokens confirmed:
    - `gate window`
    - `max pages`
    - `co_gate_window_select`
    - `co_gate_pages_select`
    - `+page`
    - `gateOpenHandler(row, gateLookupOptions)`

## Web E2E Graph Timeline Row-Window Virtualization + Pref Persistence (M17.17)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - row-window/persistence frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8148/8128)` + token grep (`curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - persistence tokens confirmed:
    - `CONTRACT_OVERLAY_PREFS_KEY`
    - `loadContractOverlayPrefs`
    - `saveContractOverlayPrefs`
  - row-window tokens confirmed:
    - `rows/window`
    - `co_row_window_select`
    - `co_row_window_top`
    - `co_row_window_prev`
    - `co_row_window_next`
    - `visibleRows`

## Web E2E Graph Overlay Shortcuts + Presets (M17.18)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - shortcut/preset frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8149/8129)` + token grep (`curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - preset/reset tokens confirmed:
    - `Preset: Triage`
    - `Preset: Deep`
    - `Reset Preset`
    - `applyOverlayPreset`
  - shortcut tokens confirmed:
    - `Shortcuts: on`
    - `Shortcuts: off`
    - `Shortcuts: h(`
    - `isEditableElementTarget`
    - `key === "1"`
    - `key === "2"`
    - `key === "0"`

## Web E2E Graph Row Detail Lazy-Expansion (M17.19)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass (3rd run)
- Notes:
  - 첫 2회 실행에서 async cancel 타이밍/HTTP 400 간헐 이슈 발생, 재실행 pass (known flaky cancel path)
  - row-detail lazy-expansion frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8150/8130)` + token grep (`curl /frontend/graph_lab/panels.mjs`, `curl /frontend/graph_lab_reactflow.html`)
- Result: pass
- Notes:
  - row-detail control tokens confirmed:
    - `Expand Visible`
    - `Collapse Details`
    - `Details`
    - `Hide`
  - lazy-detail/runtime tokens confirmed:
    - `buildContractRowKey`
    - `formatRowDetailText`
    - `toggleRowExpanded`
    - `key === "e"`
    - `key === "x"`
  - style tokens confirmed:
    - `contract-row-detail-btn`
    - `contract-overlay-row-detail`

## Web E2E Graph Overlay Shortcut Remap + Profile Persistence (M17.20)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - shortcut remap/profile frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8151/8131)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`, `curl /frontend/graph_lab_reactflow.html`)
- Result: pass
- Notes:
  - shortcut profile persistence tokens confirmed:
    - `CONTRACT_OVERLAY_SHORTCUT_PROFILES_KEY`
    - `loadShortcutProfiles`
    - `saveShortcutProfiles`
  - dynamic shortcut dispatch tokens confirmed:
    - `shortcutActionByKey`
    - `triggerShortcutAction`
    - `shortcutHintText`
  - profile/remap UI tokens confirmed:
    - `co_shortcut_profile_select`
    - `Load Profile`
    - `Save Profile`
    - `Delete Profile`
    - `Shortcut conflict`

## Web E2E Graph Row Detail Field-Level Toggles (M17.21)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - row-detail field-toggle frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8152/8132)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - field-toggle state/preset tokens confirmed:
    - `DETAIL_FIELD_DEFS`
    - `DEFAULT_DETAIL_FIELD_STATES`
    - `detailFieldStates`
    - `applyDetailFieldPreset`
    - `toggleDetailField`
  - field-toggle UI tokens confirmed:
    - `co_detail_fields_cfg`
    - `Core Fields`
    - `All Fields`
    - `selected`
  - detail renderer gating tokens confirmed:
    - `formatRowDetailText`
    - `detailFieldStates.timestamp_iso`
    - `detailFieldStates.event_meta`
    - `detailFieldStates.delta`
    - `detailFieldStates.snapshot`
    - `detailFieldStates.baseline`
    - `detailFieldStates.note_json`

## Web E2E Graph Shortcut Profile Transfer Import/Export (M17.22)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - shortcut profile transfer frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8153/8133)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - transfer helper/parser tokens confirmed:
    - `buildShortcutProfileExportBundle`
    - `serializeShortcutProfileExportBundle`
    - `parseShortcutProfileImportText`
    - `schema_version`
    - `graph_lab_contract_overlay_shortcut_profiles`
  - transfer UI tokens confirmed:
    - `co_shortcut_transfer_cfg`
    - `Export Profiles`
    - `Copy Profiles`
    - `Load JSON`
    - `Import Profiles`
    - `co_shortcut_transfer_text`
    - `co_shortcut_transfer_status`

## Web E2E Graph Detail Copy Ergonomics (M17.23)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - detail copy ergonomics frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8154/8134)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - detail copy helpers/status tokens confirmed:
    - `detailCopyStatus`
    - `copyTextToClipboard`
    - `copyVisibleDetailRows`
    - `copySingleRowDetails`
    - `co_detail_copy_status`
  - detail copy UI action tokens confirmed:
    - `co_copy_visible_details`
    - `Copy Visible`
    - `co_row_copy_compact_`
    - `co_row_copy_`
    - `co_row_copy_only_`
    - `detail_copy:`

## Web E2E Graph Severity-First Triage Filter (M17.24)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - severity triage filter frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8155/8135)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - severity filter state/model tokens confirmed:
    - `severityFilter`
    - `SEVERITY_FILTER_OPTIONS`
    - `scopedRows`
    - `severityCounts`
  - severity filter UI tokens confirmed:
    - `co_severity_select`
    - `co_sev_btn_high`
    - `co_sev_btn_med`
    - `co_sev_btn_low`
    - `filtered/scoped/all`
  - preset integration token confirmed:
    - `setSeverityFilter("high")`

## Web E2E Graph Policy-First Triage Filter (M17.25)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass (2nd run)
- Notes:
  - 첫 실행에서 async cancel 상태 assertion 간헐 실패, 즉시 재실행 pass (known flaky cancel path)
  - policy triage filter frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8156/8136)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - policy filter state/model tokens confirmed:
    - `policyFilter`
    - `POLICY_FILTER_OPTIONS`
    - `classifyPolicyState`
    - `policyCounts`
  - policy filter UI tokens confirmed:
    - `co_policy_select`
    - `co_pol_btn_hold`
    - `co_pol_btn_adopt`
    - `co_pol_btn_none`
    - `policy/severity/scoped/all`
  - preset integration token confirmed:
    - `setPolicyFilter("hold")`

## Web E2E Graph Filter Summary + Filter-Only Reset (M17.26)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - filter-summary/reset frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8157/8137)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - filter summary/reset tokens confirmed:
    - `resetOverlayFilters`
    - `activeFilterTokens`
    - `co_filter_summary`
    - `co_filter_summary_label`
    - `co_filter_summary_none`
    - `co_filter_token_`
    - `co_reset_filters`
  - filter quick-map scope token confirmed:
    - `policy/severity/scoped/all`
    - `["all", "high", "med", "low"]`
    - `["all", "hold", "adopt", "none"]`

## Web E2E Graph Filter Preset Profiles (M17.27)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - filter preset profile frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8158/8138)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - filter preset storage/normalization tokens confirmed:
    - `CONTRACT_OVERLAY_FILTER_PRESETS_KEY`
    - `DEFAULT_FILTER_PRESETS`
    - `normalizeFilterPresetName`
    - `normalizeFilterPresetConfig`
    - `loadFilterPresets`
    - `saveFilterPresets`
  - filter preset runtime/UI tokens confirmed:
    - `activeFilterPreset`
    - `filterPresetDraft`
    - `co_filter_preset_cfg`
    - `co_filter_preset_select`
    - `Load Filter Preset`
    - `Save Filter Preset`
    - `Delete Filter Preset`
    - `preset: built-in`
    - `preset: custom`

## Web E2E Graph Filter Preset Transfer Import/Export (M17.28)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - filter preset transfer frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8159/8139)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - filter transfer helper/parser tokens confirmed:
    - `buildFilterPresetExportBundle`
    - `serializeFilterPresetExportBundle`
    - `parseFilterPresetImportText`
    - `schema_version`
    - `graph_lab_contract_overlay_filter_presets`
  - filter transfer UI tokens confirmed:
    - `co_filter_transfer_cfg`
    - `Export Filter Presets`
    - `Copy Filter Presets`
    - `Load Filter JSON`
    - `Import Filter Presets`
    - `co_filter_transfer_text`
    - `co_filter_transfer_status`

## Web E2E Graph Filter Preset Import Guardrails (M17.29)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - import guardrail frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8160/8140)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - guardrail mode/preview tokens confirmed:
    - `FILTER_IMPORT_MODE_OPTIONS`
    - `normalizeFilterImportMode`
    - `filterImportMode`
    - `filterImportPreview`
    - `co_filter_import_mode_select`
    - `co_filter_import_preview`
  - safety behavior tokens confirmed:
    - `replace_custom`
    - `disabled: String(filterTransferText || \"\").trim().length === 0 || !filterImportPreviewIsValid`
    - `graph_lab_contract_overlay_filter_presets`

## Web E2E Graph Selective Filter Preset Import + Dry-Run Rows (M17.30)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - selective import frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8161/8141)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - selective import model tokens confirmed:
    - `parsedFilterImportPayload`
    - `filterImportRows`
    - `selectedFilterImportNames`
    - `import skipped: no presets selected`
  - selective import UI tokens confirmed:
    - `co_filter_import_select_all`
    - `co_filter_import_select_none`
    - `co_filter_import_rows`
    - `co_filter_import_row_`
  - dry-run preview tokens confirmed:
    - `selected 0`
    - `select presets to import`
    - `replace_custom`

## Web E2E Graph Replace Import Confirmation + Undo (M17.31)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - replace-confirm/undo frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8162/8142)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - replace-confirm/undo model tokens confirmed:
    - `cloneNormalizedFilterPresets`
    - `filterReplaceConfirmChecked`
    - `filterImportUndoSnapshot`
    - `undoLastFilterImport`
    - `replaceImportNeedsConfirmation`
  - replace-confirm/undo UI/status tokens confirmed:
    - `co_filter_replace_confirm`
    - `co_filter_import_undo`
    - `co_filter_import_undo_hint`
    - `confirm required: enable replace confirmation for replace custom`
    - `undo restored snapshot`

## Web E2E Graph Import Audit Trail + Multi-Level Undo/Redo (M17.32)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - import-audit/undo-redo frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8163/8143)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - audit/stack model tokens confirmed:
    - `buildFilterPresetStateSnapshot`
    - `compactNameList`
    - `filterImportUndoStack`
    - `filterImportRedoStack`
    - `filterImportAuditTrail`
    - `redoLastFilterImport`
  - UI/status/audit tokens confirmed:
    - `co_filter_import_undo`
    - `co_filter_import_redo`
    - `co_filter_import_audit`
    - `co_filter_import_audit_row_`
    - `undo/redo depth`
    - `redo restored snapshot`
    - `kind: "import"`
    - `kind: "undo"`
    - `kind: "redo"`

## Web E2E Graph Audit Drilldown + Import-History Persistence (M17.33)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - audit-drilldown/persistence frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8164/8144)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - import-history persistence tokens confirmed:
    - `CONTRACT_OVERLAY_FILTER_IMPORT_HISTORY_KEY`
    - `loadFilterImportHistoryState`
    - `saveFilterImportHistoryState`
    - `buildFilterImportAuditExportBundle`
    - `serializeFilterImportAuditExportBundle`
  - audit drilldown tokens confirmed:
    - `activeFilterImportAuditId`
    - `buildFilterImportAuditDetailText`
    - `co_filter_import_audit_controls`
    - `co_filter_import_audit_copy`
    - `co_filter_import_audit_export`
    - `co_filter_import_audit_rows`
    - `co_filter_import_audit_detail`
    - `co_filter_import_audit_row_`
    - `names:`

## Web E2E Graph Import History Maintenance + Audit Search/Filter (M17.34)

- Date: 2026-02-22
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - import-history maintenance/audit-filter frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-22
- Command: `python3 api/ui local smoke (8165/8145)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - history maintenance tokens confirmed:
    - `clearFilterImportHistory`
    - `pruneFilterImportHistory`
    - `co_filter_import_prune_keep`
    - `co_filter_import_prune`
    - `co_filter_import_clear`
  - audit search/filter tokens confirmed:
    - `filterImportAuditRowsFiltered`
    - `co_filter_import_audit_search`
    - `co_filter_import_audit_kind`
    - `co_filter_import_audit_mode`
    - `co_filter_import_audit_count`
    - `no audit rows matched current filters`

## Web E2E Graph Audit Reset UX + Row-Volume Guardrails (M17.35)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - audit-reset/row-volume-guard frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8166/8146)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - row-volume guard tokens confirmed:
    - `CONTRACT_ROW_VOLUME_GUARD_TRIGGER`
    - `CONTRACT_ROW_VOLUME_GUARD_MAX_WINDOW`
    - `rowVolumeGuardBypass`
    - `rowVolumeGuardActive`
    - `rowWindowOptionValues`
    - `co_row_volume_guard_bypass`
    - `co_row_volume_guard_hint`
    - `rows_guard:off`
  - audit query reset tokens confirmed:
    - `resetFilterImportAuditQuery`
    - `filterImportAuditQueryActive`
    - `co_filter_import_audit_reset`

## Web E2E Graph Audit Pagination Cap + Query Preset Shortcuts (M17.36)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - audit-pagination/preset frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - first attempt observed transient async-cancel timing race in validation script; immediate re-run passed without code changes

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8167/8147)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - audit pagination cap tokens confirmed:
    - `FILTER_IMPORT_AUDIT_ROW_CAP_OPTIONS`
    - `filterImportAuditRowCapText`
    - `filterImportAuditRowOffset`
    - `filterImportAuditRowsVisible`
    - `filterImportAuditMaxOffset`
    - `filterImportAuditRowEnd`
    - `co_filter_import_audit_row_cap`
    - `co_filter_import_audit_top`
    - `co_filter_import_audit_prev`
    - `co_filter_import_audit_next`
    - `co_filter_import_audit_window_hint`
  - audit query preset tokens confirmed:
    - `FILTER_IMPORT_AUDIT_QUERY_PRESETS`
    - `activeFilterImportAuditQueryPresetId`
    - `applyFilterImportAuditQueryPreset`
    - `co_filter_import_audit_preset_`

## Web E2E Graph Audit Deep-Link Bundle + Preset Pinning (M17.37)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - audit-deeplink/preset-pin frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8168/8148)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - deep-link bundle tokens confirmed:
    - `buildFilterImportAuditDeepLinkBundle`
    - `serializeFilterImportAuditDeepLinkBundle`
    - `copyFilterImportAuditDeepLinkBundle`
    - `co_filter_import_audit_copy_deeplink`
  - preset pinning tokens confirmed:
    - `resolveFilterImportAuditQueryPreset`
    - `filterImportAuditPinnedPresetId`
    - `filterImportAuditPinnedPresetActive`
    - `toggleFilterImportAuditPinnedPreset`
    - `filterImportAuditPresetPinnable`
    - `co_filter_import_audit_preset_pin`
    - `co_filter_import_audit_preset_pin_hint`
    - `filterImportAuditPinnedPreset`
    - `audit query preset pinned`
    - `audit query preset unpinned`
    - `audit query reset -> pinned`

## Web E2E Graph Audit Bundle Restore + Shortcut Pin Toggle (M17.38)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - audit-bundle-restore/shortcut-pin-toggle frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8169/8149)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - bundle restore tokens confirmed:
    - `parseFilterImportAuditDeepLinkBundleText`
    - `parsedFilterImportAuditDeepLinkPayload`
    - `filterImportAuditDeepLinkPreview`
    - `applyFilterImportAuditDeepLinkBundleFromText`
    - `co_filter_import_audit_bundle_preview`
    - `co_filter_import_audit_apply_deeplink`
    - `audit bundle apply failed`
    - `audit deep-link bundle applied`
  - shortcut pin toggle tokens confirmed:
    - `audit_pin_toggle`
    - `triggerShortcutAction`
    - `toggleFilterImportAuditPinnedPreset`

## Web E2E Graph Audit Bundle Schema Guardrails + Operator Hints (M17.39)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - audit-bundle-schema/operator-hint frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8170/8150)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - schema guardrail tokens confirmed:
    - `FILTER_IMPORT_AUDIT_DEEPLINK_KIND`
    - `FILTER_IMPORT_AUDIT_DEEPLINK_SCHEMA_VERSION`
    - `schema_version missing`
    - `unsupported schema_version`
  - operator hint tokens confirmed:
    - `co_filter_import_audit_bundle_schema_hint`
    - `co_filter_import_audit_preset_active_hint`
    - `co_filter_import_audit_shortcut_hint`
    - `audit bundle expects kind=`
    - `pin shortcut:`

## Web E2E Graph Audit Partial-Restore Toggles + Pin State Chips (M17.40)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - audit-partial-restore/pin-chip frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8171/8151)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - partial-restore toggle tokens confirmed:
    - `filterImportAuditRestoreQueryChecked`
    - `filterImportAuditRestorePagingChecked`
    - `filterImportAuditRestorePinnedPresetChecked`
    - `filterImportAuditRestoreActiveEntryChecked`
    - `co_filter_import_audit_restore_scopes`
    - `co_filter_import_audit_restore_query`
    - `co_filter_import_audit_restore_paging`
    - `co_filter_import_audit_restore_pinned`
    - `co_filter_import_audit_restore_entry`
    - `audit bundle apply skipped: no restore scope enabled`
  - pin state chip tokens confirmed:
    - `co_filter_import_audit_pin_state_chips`
    - `co_filter_import_audit_pin_chip_pinned`
    - `co_filter_import_audit_pin_chip_active`
    - `co_filter_import_audit_pin_chip_custom`
    - `co_filter_import_audit_pin_chip_shortcut`
    - `scope:`

## Web E2E Graph Audit Restore Presets + Pin Chip Filter Controls (M17.41)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - audit-restore-presets/pin-chip-filter frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8171/8151)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - restore preset tokens confirmed:
    - `FILTER_IMPORT_AUDIT_RESTORE_PRESETS`
    - `resolveFilterImportAuditRestorePreset`
    - `activeFilterImportAuditRestorePresetId`
    - `co_filter_import_audit_restore_presets`
    - `co_filter_import_audit_restore_preset_all`
    - `co_filter_import_audit_restore_preset_query_pin`
    - `co_filter_import_audit_restore_preset_paging_entry`
    - `co_filter_import_audit_restore_preset_query_only`
    - `co_filter_import_audit_restore_preset_active`
    - `audit restore preset:`
    - `restore:`
  - pin chip filter tokens confirmed:
    - `FILTER_IMPORT_AUDIT_PIN_CHIP_FILTER_OPTIONS`
    - `normalizeFilterImportAuditPinChipFilter`
    - `filterImportAuditPinChipFilter`
    - `filterImportAuditPinChipVisibility`
    - `co_filter_import_audit_pin_chip_filters`
    - `co_filter_import_audit_pin_chip_filter_all`
    - `co_filter_import_audit_pin_chip_filter_state`
    - `co_filter_import_audit_pin_chip_filter_context`
    - `co_filter_import_audit_pin_chip_filter_shortcut`
    - `co_filter_import_audit_pin_chip_filter_active`

## Web E2E Graph Audit Scoped Quick-Apply + Operator Hints (M17.42)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - audit-quick-apply/operator-hint frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8171/8151)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - scoped quick-apply tokens confirmed:
    - `FILTER_IMPORT_AUDIT_QUICK_APPLY_OPTIONS`
    - `resolveFilterImportAuditQuickApplyOption`
    - `applyFilterImportAuditDeepLinkBundleWithScopes`
    - `applyFilterImportAuditDeepLinkQuickScope`
    - `co_filter_import_audit_apply_quick_scopes`
    - `co_filter_import_audit_apply_quick_`
    - `co_filter_import_audit_apply_quick_hint`
    - `quick apply overrides restore scope for this action`
  - restore/pin operator hint tokens confirmed:
    - `co_filter_import_audit_restore_scope_hint`
    - `co_filter_import_audit_pin_operator_hint`
    - `restore:q`

## Web E2E Graph Audit Quick-Apply Coupling + Safe Reset Affordances (M17.43)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - audit-quick-coupling/safe-reset frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8171/8151)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - quick-apply coupling tokens confirmed:
    - `filterImportAuditQuickApplySyncRestore`
    - `filterImportAuditQuickApplySyncRestoreChecked`
    - `activeFilterImportAuditQuickApplyOptionId`
    - `co_filter_import_audit_apply_quick_sync`
    - `co_filter_import_audit_apply_quick_active`
    - `quick:`
    - `sync:`
  - safe reset tokens confirmed:
    - `co_filter_import_audit_safe_reset_controls`
    - `co_filter_import_audit_reset_arm`
    - `co_filter_import_audit_reset_restore_scope`
    - `co_filter_import_audit_reset_pin_context`
    - `co_filter_import_audit_reset_operator_context`
    - `co_filter_import_audit_reset_hint`
    - `reset blocked: arm reset first`
    - `audit restore scope reset`
    - `audit pin context reset`
    - `audit operator context reset`

## Web E2E Graph Audit Quick Telemetry + Guided Reset Hint (M17.44)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - audit-quick-telemetry/guided-reset frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8171/8151)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - quick telemetry tokens confirmed:
    - `FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_LIMIT`
    - `normalizeFilterImportAuditQuickApplyTelemetryEntry`
    - `buildFilterImportAuditQuickApplyTelemetryBundle`
    - `serializeFilterImportAuditQuickApplyTelemetryBundle`
    - `filterImportAuditQuickApplyTelemetry`
    - `filterImportAuditQuickApplyTelemetrySummary`
    - `co_filter_import_audit_quick_telemetry_controls`
    - `co_filter_import_audit_quick_telemetry_copy`
    - `co_filter_import_audit_quick_telemetry_export`
    - `co_filter_import_audit_quick_telemetry_clear`
    - `co_filter_import_audit_quick_telemetry_summary`
  - guided reset hint tokens confirmed:
    - `FILTER_IMPORT_AUDIT_RESET_ARM_TIMEOUT_MS`
    - `filterImportAuditResetGuidedHint`
    - `co_filter_import_audit_reset_guided_hint`
    - `reset arm expired: re-arm to execute reset`
    - `reset armed: choose reset action within 20s`
    - `quick-telemetry total:`

## Web E2E Graph Audit Telemetry Trend Chips + Safe Reset Copy Refinement (M17.45)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - telemetry-trend/reset-copy frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8171/8151)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - telemetry trend chip tokens confirmed:
    - `FILTER_IMPORT_AUDIT_QUICK_TREND_WINDOW`
    - `filterImportAuditQuickTelemetryTrend`
    - `co_filter_import_audit_quick_telemetry_trend_chips`
    - `co_filter_import_audit_quick_telemetry_chip_recent_rate`
    - `co_filter_import_audit_quick_telemetry_chip_fail_streak`
    - `co_filter_import_audit_quick_telemetry_chip_sync_rate`
    - `co_filter_import_audit_quick_telemetry_chip_latest_reason`
    - `recent-ok:`
    - `fail-streak:`
    - `sync-applied:`
  - safe reset copy/countdown tokens confirmed:
    - `safe reset guide: armed (`
    - `safe reset armed`
    - `reset blocked: arm reset first (safe window required)`
    - `reset armed: choose reset action within 20s (safe window active)`
    - `reset disarmed: safe reset idle`
    - `audit restore scope reset (safe reset consumed)`
    - `audit pin context reset (safe reset consumed)`
    - `audit operator context reset (safe reset consumed)`

## Web E2E Graph Audit Quick Telemetry Drilldown Controls (M17.46)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - telemetry-drilldown frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8171/8151)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - telemetry drilldown derivation tokens confirmed:
    - `FILTER_IMPORT_AUDIT_QUICK_REASON_CHIP_LIMIT`
    - `FILTER_IMPORT_AUDIT_QUICK_REASON_QUERY_MAX`
    - `filterImportAuditQuickTelemetryReasonQueryNormalized`
    - `filterImportAuditQuickTelemetryRowsDrilldown`
    - `filterImportAuditQuickTelemetryReasonChips`
    - `filterImportAuditQuickTelemetryDrilldownSummary`
    - `clearFilterImportAuditQuickTelemetryDrilldown`
  - failures-only/reason-focus UI tokens confirmed:
    - `co_filter_import_audit_quick_telemetry_drilldown_controls`
    - `co_filter_import_audit_quick_telemetry_drilldown_failure_only`
    - `co_filter_import_audit_quick_telemetry_drilldown_reason_query`
    - `co_filter_import_audit_quick_telemetry_drilldown_clear`
    - `co_filter_import_audit_quick_telemetry_drilldown_summary`
    - `co_filter_import_audit_quick_telemetry_reason_chips`
    - `co_filter_import_audit_quick_telemetry_reason_chip_`
    - `failures-only`
    - `reason focus:`
    - `Reset Drilldown`
    - `drilldown `

## Web E2E Graph Audit Quick Telemetry Drilldown Presets + Handoff Bundle (M17.47)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - telemetry-drilldown-preset/handoff frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8171/8151)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - drilldown preset/handoff bundle tokens confirmed:
    - `FILTER_IMPORT_AUDIT_QUICK_DRILLDOWN_PRESETS`
    - `resolveFilterImportAuditQuickDrilldownPreset`
    - `buildFilterImportAuditQuickTelemetryDrilldownBundle`
    - `serializeFilterImportAuditQuickTelemetryDrilldownBundle`
    - `activeFilterImportAuditQuickTelemetryDrilldownPresetId`
    - `applyFilterImportAuditQuickTelemetryDrilldownPreset`
    - `applyFilterImportAuditQuickTelemetryReasonChip`
    - `graph_lab_contract_overlay_filter_import_quick_apply_telemetry_drilldown`
  - drilldown copy/export controls confirmed:
    - `co_filter_import_audit_quick_telemetry_drilldown_presets`
    - `co_filter_import_audit_quick_telemetry_drilldown_preset_`
    - `co_filter_import_audit_quick_telemetry_drilldown_copy`
    - `co_filter_import_audit_quick_telemetry_drilldown_export`
    - `co_filter_import_audit_quick_telemetry_drilldown_preset_active`
    - `Copy Drilldown JSON`
    - `Export Drilldown JSON`
    - `drilldown preset:`

## Web E2E Graph Audit Quick Telemetry Custom Profile Save/Load + Team Transfer (M17.48)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - telemetry-drilldown-profile frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8171/8151)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - custom profile model/save-load tokens confirmed:
    - `CONTRACT_OVERLAY_QUICK_TELEMETRY_DRILLDOWN_PROFILES_KEY`
    - `DEFAULT_FILTER_IMPORT_AUDIT_QUICK_TELEMETRY_DRILLDOWN_PROFILES`
    - `normalizeQuickTelemetryDrilldownProfileName`
    - `normalizeQuickTelemetryDrilldownProfile`
    - `loadQuickTelemetryDrilldownProfiles`
    - `saveQuickTelemetryDrilldownProfiles`
    - `quickTelemetryDrilldownProfiles`
    - `activeQuickTelemetryDrilldownProfile`
    - `quickTelemetryDrilldownProfileDraft`
    - `applyActiveQuickTelemetryDrilldownProfile`
    - `saveCurrentQuickTelemetryDrilldownProfile`
    - `deleteActiveQuickTelemetryDrilldownProfile`
  - team transfer tokens confirmed:
    - `buildQuickTelemetryDrilldownProfileExportBundle`
    - `serializeQuickTelemetryDrilldownProfileExportBundle`
    - `parseQuickTelemetryDrilldownProfileImportText`
    - `graph_lab_contract_overlay_quick_telemetry_drilldown_profiles`
    - `co_filter_import_audit_quick_telemetry_profile_transfer_cfg`
    - `co_filter_import_audit_quick_telemetry_profile_export`
    - `co_filter_import_audit_quick_telemetry_profile_copy`
    - `co_filter_import_audit_quick_telemetry_profile_load_json`
    - `co_filter_import_audit_quick_telemetry_profile_import`
    - `co_filter_import_audit_quick_telemetry_profile_transfer_text`
    - `drilldown profile transfer:`

## Web E2E Graph Audit Quick Telemetry Profile Import Guardrails + Rollback Hint (M17.49)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - telemetry-profile-import-guardrail frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `python3 api/ui local smoke (8171/8151)` + token grep (`curl /health`, `curl /frontend/graph_lab/panels.mjs`)
- Result: pass
- Notes:
  - guardrail derivation tokens confirmed:
    - `cloneNormalizedQuickTelemetryDrilldownProfiles`
    - `quickTelemetryDrilldownImportOverwriteConfirmChecked`
    - `quickTelemetryDrilldownImportUndoSnapshot`
    - `parsedQuickTelemetryDrilldownProfileImportPayload`
    - `quickTelemetryDrilldownImportRows`
    - `quickTelemetryDrilldownImportHasChangedOverwrite`
    - `quickTelemetryDrilldownImportPreview`
    - `quickTelemetryDrilldownImportRollbackHint`
    - `undoLastQuickTelemetryDrilldownProfileImport`
    - `import blocked: confirm overwrite changed profiles`
    - `rollback: undo available`
  - UI tokens confirmed:
    - `co_filter_import_audit_quick_telemetry_profile_import_confirm_label`
    - `co_filter_import_audit_quick_telemetry_profile_import_preview`
    - `co_filter_import_audit_quick_telemetry_profile_import_rollback_hint`
    - `co_filter_import_audit_quick_telemetry_profile_import_undo`
    - `co_filter_import_audit_quick_telemetry_profile_import_preview_row_`

## Web E2E Graph Audit Quick Telemetry Profile Selective Import + Conflict-Only View (M17.50)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - telemetry-profile-selective-import frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `rg -n "quickTelemetryDrilldownImportSelection|quickTelemetryDrilldownImportConflictOnlyChecked|quickTelemetryDrilldownImportRowsVisible|quickTelemetryDrilldownImportSelectionRows|selectedQuickTelemetryDrilldownImportNames|toggleQuickTelemetryDrilldownImportSelection|selectAllQuickTelemetryDrilldownImportRowsVisible|clearQuickTelemetryDrilldownImportSelection|import skipped: select profiles|co_filter_import_audit_quick_telemetry_profile_import_conflict_only|co_filter_import_audit_quick_telemetry_profile_import_select_all|co_filter_import_audit_quick_telemetry_profile_import_select_none|co_filter_import_audit_quick_telemetry_profile_import_rows|import rows: no matches in current view" /Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
- Result: pass
- Notes:
  - selective-import/conflict-only derivation tokens confirmed:
    - `quickTelemetryDrilldownImportSelection`
    - `quickTelemetryDrilldownImportConflictOnlyChecked`
    - `quickTelemetryDrilldownImportRowsVisible`
    - `quickTelemetryDrilldownImportSelectionRows`
    - `selectedQuickTelemetryDrilldownImportNames`
    - `toggleQuickTelemetryDrilldownImportSelection`
    - `selectAllQuickTelemetryDrilldownImportRowsVisible`
    - `clearQuickTelemetryDrilldownImportSelection`
    - `import skipped: select profiles`
  - UI tokens confirmed:
    - `co_filter_import_audit_quick_telemetry_profile_import_conflict_only`
    - `co_filter_import_audit_quick_telemetry_profile_import_select_all`
    - `co_filter_import_audit_quick_telemetry_profile_import_select_none`
    - `co_filter_import_audit_quick_telemetry_profile_import_rows`
    - `co_filter_import_audit_quick_telemetry_profile_import_rows_empty`
    - `import rows: no matches in current view`

## Web E2E Graph Audit Quick Telemetry Profile Import Pagination + Selection Safety (M17.51)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - telemetry-profile-import-pagination frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `rg -n "QUICK_TELEMETRY_DRILLDOWN_IMPORT_ROW_CAP_OPTIONS|quickTelemetryDrilldownImportRowCapText|quickTelemetryDrilldownImportRowCap|quickTelemetryDrilldownImportRowOffset|quickTelemetryDrilldownImportMaxOffset|quickTelemetryDrilldownImportRowEnd|quickTelemetryDrilldownImportRowsPage|quickTelemetryDrilldownImportSelectionSafetyHint|quickTelemetryDrilldownImportSelectedOffPageCount|quickTelemetryDrilldownImportHiddenSelectionCount|selectPageQuickTelemetryDrilldownImportSelection|clearPageQuickTelemetryDrilldownImportSelection|co_filter_import_audit_quick_telemetry_profile_import_row_cap|co_filter_import_audit_quick_telemetry_profile_import_page_top|co_filter_import_audit_quick_telemetry_profile_import_page_prev|co_filter_import_audit_quick_telemetry_profile_import_page_next|co_filter_import_audit_quick_telemetry_profile_import_select_page|co_filter_import_audit_quick_telemetry_profile_import_clear_page|co_filter_import_audit_quick_telemetry_profile_import_selection_safety|co_filter_import_audit_quick_telemetry_profile_import_page_hint" /Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
- Result: pass
- Notes:
  - pagination/window derivation tokens confirmed:
    - `QUICK_TELEMETRY_DRILLDOWN_IMPORT_ROW_CAP_OPTIONS`
    - `quickTelemetryDrilldownImportRowCapText`
    - `quickTelemetryDrilldownImportRowCap`
    - `quickTelemetryDrilldownImportRowOffset`
    - `quickTelemetryDrilldownImportMaxOffset`
    - `quickTelemetryDrilldownImportRowEnd`
    - `quickTelemetryDrilldownImportRowsPage`
  - selection safety tokens confirmed:
    - `quickTelemetryDrilldownImportSelectionSafetyHint`
    - `quickTelemetryDrilldownImportSelectedOffPageCount`
    - `quickTelemetryDrilldownImportHiddenSelectionCount`
    - `selectPageQuickTelemetryDrilldownImportSelection`
    - `clearPageQuickTelemetryDrilldownImportSelection`
  - UI tokens confirmed:
    - `co_filter_import_audit_quick_telemetry_profile_import_row_cap`
    - `co_filter_import_audit_quick_telemetry_profile_import_page_top`
    - `co_filter_import_audit_quick_telemetry_profile_import_page_prev`
    - `co_filter_import_audit_quick_telemetry_profile_import_page_next`
    - `co_filter_import_audit_quick_telemetry_profile_import_select_page`
    - `co_filter_import_audit_quick_telemetry_profile_import_clear_page`
    - `co_filter_import_audit_quick_telemetry_profile_import_page_hint`
    - `co_filter_import_audit_quick_telemetry_profile_import_selection_safety`

## Web E2E Graph Audit Quick Telemetry Profile Import Query/Filter Aids (M17.52)

- Date: 2026-02-23
- Command: `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py`
- Result: pass
- Notes:
  - telemetry-profile-import-query-filter frontend 변경 이후에도 graph run/cancel/retry/baseline/policy/regression API regression suite pass
  - backend API contracts and response schema stability 유지 확인

- Date: 2026-02-23
- Command: `rg -n "QUICK_TELEMETRY_DRILLDOWN_IMPORT_NAME_QUERY_MAX|QUICK_TELEMETRY_DRILLDOWN_IMPORT_CONFLICT_FILTER_OPTIONS|normalizeQuickTelemetryDrilldownImportConflictFilter|matchQuickTelemetryDrilldownImportConflictFilter|quickTelemetryDrilldownImportNameQuery|quickTelemetryDrilldownImportConflictFilter|quickTelemetryDrilldownImportRowsByQuery|quickTelemetryDrilldownImportConflictFilterCounts|co_filter_import_audit_quick_telemetry_profile_import_name_query|co_filter_import_audit_quick_telemetry_profile_import_filter_reset|co_filter_import_audit_quick_telemetry_profile_import_conflict_filter_chips|co_filter_import_audit_quick_telemetry_profile_import_conflict_filter_chip_" /Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`
- Result: pass
- Notes:
  - query/filter model tokens confirmed:
    - `QUICK_TELEMETRY_DRILLDOWN_IMPORT_NAME_QUERY_MAX`
    - `QUICK_TELEMETRY_DRILLDOWN_IMPORT_CONFLICT_FILTER_OPTIONS`
    - `normalizeQuickTelemetryDrilldownImportConflictFilter`
    - `matchQuickTelemetryDrilldownImportConflictFilter`
    - `quickTelemetryDrilldownImportNameQuery`
    - `quickTelemetryDrilldownImportConflictFilter`
    - `quickTelemetryDrilldownImportRowsByQuery`
    - `quickTelemetryDrilldownImportConflictFilterCounts`
  - UI tokens confirmed:
    - `co_filter_import_audit_quick_telemetry_profile_import_name_query`
    - `co_filter_import_audit_quick_telemetry_profile_import_filter_reset`
    - `co_filter_import_audit_quick_telemetry_profile_import_conflict_filter_chips`
    - `co_filter_import_audit_quick_telemetry_profile_import_conflict_filter_chip_`
