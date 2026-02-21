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
  - Profile evaluation path pass (`good -> pass`, `bad -> fail`)
  - Threshold derivation from train candidates and reference snapshot pass
