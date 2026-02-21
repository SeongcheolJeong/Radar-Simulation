# Paper Traceability Matrix (HybridDynamicRT)

## Scope

This document maps paper-level requirements to current repository implementation and validation artifacts.

Paper reference:

- IEEE Xplore document: `10559769`
- URL: `https://ieeexplore.ieee.org/document/10559769/`

## Interpretation Note

- The mapping is based on:
  - paper abstract/summary level statements
  - HybridDynamicRT public repository structure
  - current implementation in this repository
- Since the full private/internal source is not fully visible, some rows are marked as `Partial` or `Planned` by inference.

## Status Legend

- `Implemented`: code path and validation command exist in this repository
- `Partial`: baseline implementation exists but paper-level fidelity is not fully matched
- `Planned`: not implemented yet

## Matrix

| ID | Paper Requirement (Condensed) | Status | Code Path(s) | Validation / Evidence | Notes |
|---|---|---|---|---|---|
| R1 | Dynamic RT/Blender frame ingestion for scenario rendering outputs | Implemented | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/adapters/hybriddynamicrt_frames.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/pipeline.py` | `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_frame_adapter.py`, `.../scripts/validate_hybrid_pipeline_output.py` | Supports `AmplitudeOutput####` + `DistanceOutput####`/`Depth####` |
| R2 | FMCW beat-signal generation from path/range information | Implemented | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/synth.py` | `.../scripts/validate_step1.py` | Canonical ADC output `adc[sample, chirp, tx, rx]` |
| R3 | TDM-MIMO handling and virtual array compatible processing | Implemented | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/synth.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/pipeline.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/motion_compensation.py` | `.../scripts/validate_step1.py`, `.../scripts/validate_adapter_smoke.py`, `.../scripts/validate_motion_compensation_core.py`, `.../scripts/validate_hybrid_ingest_cli_with_motion_comp.py` | TDM schedule explicit via `tx_schedule`, baseline motion compensation added |
| R4 | Range-Doppler image generation | Implemented | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/hybrid_pcode.py` (`doppler_estimation_from_channel`) | `.../scripts/validate_hybrid_doppler_estimation.py` | P-code replacement P2 |
| R5 | Doppler summary descriptors/concatenation over range | Implemented | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/hybrid_pcode.py` (`generate_concatenated_doppler`) | `.../scripts/validate_hybrid_concatenated_dop.py` | P-code replacement P3 |
| R6 | Range-Angle / angle estimation from MIMO channel | Implemented | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/hybrid_pcode.py` (`angle_estimation_from_channel`) | `.../scripts/validate_hybrid_angle_estimation.py` | P-code replacement P4 |
| R7 | Channel generation core from dynamic range/velocity evolution | Implemented | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/hybrid_pcode.py` (`generate_channel_from_distances`) | `.../scripts/validate_hybrid_generate_channel.py` | P-code replacement P1 |
| R8 | Reflection/scattering path power modeling | Partial | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/hybrid_pcode.py` (`calculate_reflecting_path_power`, `calculate_scattering_path_power`), `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/path_power_tuning.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/adapters/hybriddynamicrt_frames.py` | `.../scripts/validate_hybrid_path_power_models.py`, `.../scripts/validate_path_power_tuning.py`, `.../scripts/validate_hybrid_ingest_cli_with_path_power_fit.py` | Physics-consistent replacement + tuning + ingest integration implemented; real measured calibration CSV fitting is pending |
| R9 | End-to-end integrated estimation flow (channel -> RD/RA summaries) | Implemented | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/hybrid_pcode.py` (`run_hybrid_estimation_bundle`), `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/pipeline.py` | `.../scripts/validate_hybrid_pcode_bundle.py`, `.../scripts/validate_hybrid_ingest_cli_with_bundle.py` | Optional CLI output `hybrid_estimation.npz` |
| R10 | Antenna pattern-aware modeling (paper-level higher-fidelity scenario) | Partial | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/ffd.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/antenna.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/synth.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/pipeline.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/calibration.py` | `.../scripts/validate_ffd_parser.py`, `.../scripts/validate_ffd_real_sample_regression.py`, `.../scripts/validate_ffd_pipeline_integration.py`, `.../scripts/validate_hybrid_ingest_cli_with_ffd.py`, `.../scripts/validate_jones_polarization_flow.py`, `.../scripts/validate_global_jones_calibration.py`, `.../scripts/validate_hybrid_ingest_cli_with_global_jones.py` | `.ffd` baseline + Jones flow + global Jones calibration bootstrap integrated; measured-data calibration is pending |
| R11 | Measurement-level parity checks vs chamber/corridor datasets | Partial | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/parity.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/calibration.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/calibration_samples.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/measurement_csv.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/scenario_profile.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/motion_tuning.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/replay_batch.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/profile_lock.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/measured_replay.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/measured_pack_discovery.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/replay_manifest_builder.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/adc_pack_builder.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/mat_adc_extract.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/compare_hybrid_estimation_parity.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_calibration_samples_from_outputs.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_calibration_samples_from_measurement_csv.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_scenario_profile.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/evaluate_scenario_profile.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_moving_target_replay_batch.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/finalize_scenario_profile_lock.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_measured_replay_execution.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_measured_replay_plan.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_replay_manifest_from_pack.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/generate_mock_measured_packs.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_pack_from_adc_npz_dir.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/extract_mat_adc_to_npz.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_dataset_onboarding_pipeline.py` | `.../scripts/validate_parity_metrics_contract.py`, `.../scripts/validate_global_jones_calibration.py`, `.../scripts/validate_calibration_samples_builder.py`, `.../scripts/validate_measurement_csv_converter.py`, `.../scripts/validate_scenario_profile_workflow.py`, `.../scripts/validate_hybrid_ingest_cli_with_profile_defaults.py`, `.../scripts/validate_moving_target_replay_batch.py`, `.../scripts/validate_profile_lock_finalization.py`, `.../scripts/validate_measured_replay_execution.py`, `.../scripts/validate_measured_replay_plan_builder.py`, `.../scripts/validate_replay_manifest_builder.py`, `.../scripts/validate_mock_measured_packs_e2e.py`, `.../scripts/validate_adc_pack_builder.py`, `.../scripts/validate_mat_adc_extractor_core.py`, `.../scripts/validate_dataset_onboarding_pipeline.py` | Parity + calibration sample/fitting + measured CSV conversion + scenario profile lock + motion-tuning selection + replay batch automation + lock-finalization + measured multi-pack orchestration + plan/manifest auto-discovery + mock-pack bootstrap + ADC/MAT conversion + one-command onboarding scaffolding implemented; real measured dataset replay executed on Xiangyu public sequences (BMS1000/CMS1000); tuned strict lock flow validated |
| R12 | MoCap/AMASS-style human motion dataset driven scenario automation | Partial | Ingest supports frame sequences; no native MoCap import toolchain yet | Existing frame-based validations only | Dataset-level automation not yet included |

## Next Parity Steps

1. Execute measured moving-target replay batches and lock final per-scenario profiles.
2. Fit and version global Jones matrices per measured scenario pack.
3. Add scenario packs for motion classes to emulate paper-like evaluation tables.
