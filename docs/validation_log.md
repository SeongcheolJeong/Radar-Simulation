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
