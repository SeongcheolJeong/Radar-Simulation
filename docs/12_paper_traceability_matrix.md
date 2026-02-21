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
| R3 | TDM-MIMO handling and virtual array compatible processing | Implemented | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/synth.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/pipeline.py` | `.../scripts/validate_step1.py`, `.../scripts/validate_adapter_smoke.py` | TDM schedule explicit via `tx_schedule` |
| R4 | Range-Doppler image generation | Implemented | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/hybrid_pcode.py` (`doppler_estimation_from_channel`) | `.../scripts/validate_hybrid_doppler_estimation.py` | P-code replacement P2 |
| R5 | Doppler summary descriptors/concatenation over range | Implemented | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/hybrid_pcode.py` (`generate_concatenated_doppler`) | `.../scripts/validate_hybrid_concatenated_dop.py` | P-code replacement P3 |
| R6 | Range-Angle / angle estimation from MIMO channel | Implemented | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/hybrid_pcode.py` (`angle_estimation_from_channel`) | `.../scripts/validate_hybrid_angle_estimation.py` | P-code replacement P4 |
| R7 | Channel generation core from dynamic range/velocity evolution | Implemented | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/hybrid_pcode.py` (`generate_channel_from_distances`) | `.../scripts/validate_hybrid_generate_channel.py` | P-code replacement P1 |
| R8 | Reflection/scattering path power modeling | Partial | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/hybrid_pcode.py` (`calculate_reflecting_path_power`, `calculate_scattering_path_power`) | `.../scripts/validate_hybrid_path_power_models.py` | Physics-consistent replacement model, not paper-parameter tuned yet |
| R9 | End-to-end integrated estimation flow (channel -> RD/RA summaries) | Implemented | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/hybrid_pcode.py` (`run_hybrid_estimation_bundle`), `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/pipeline.py` | `.../scripts/validate_hybrid_pcode_bundle.py`, `.../scripts/validate_hybrid_ingest_cli_with_bundle.py` | Optional CLI output `hybrid_estimation.npz` |
| R10 | Antenna pattern-aware modeling (paper-level higher-fidelity scenario) | Partial | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/ffd.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/antenna.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/synth.py`, `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/pipeline.py` | `.../scripts/validate_ffd_parser.py`, `.../scripts/validate_ffd_real_sample_regression.py`, `.../scripts/validate_ffd_pipeline_integration.py`, `.../scripts/validate_hybrid_ingest_cli_with_ffd.py`, `.../scripts/validate_jones_polarization_flow.py` | `.ffd` baseline + real-sample regression + Jones-flow baseline integrated; measurement-level polarization calibration is pending |
| R11 | Measurement-level parity checks vs chamber/corridor datasets | Partial | `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/parity.py`, `/Users/seongcheoljeong/Documents/Codex_test/scripts/compare_hybrid_estimation_parity.py` | `.../scripts/validate_parity_metrics_contract.py` | RD/RA parity metrics baseline implemented; measured-dataset calibration loop is pending |
| R12 | MoCap/AMASS-style human motion dataset driven scenario automation | Partial | Ingest supports frame sequences; no native MoCap import toolchain yet | Existing frame-based validations only | Dataset-level automation not yet included |

## Next Parity Steps

1. Calibrate Jones/polarization parameters with measured chamber or trusted full-wave references.
2. Lock scenario-specific parity thresholds and archive reference `hybrid_estimation.npz` snapshots.
3. Add scenario packs for motion classes to emulate paper-like evaluation tables.
