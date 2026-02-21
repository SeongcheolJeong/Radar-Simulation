# P-code Reimplementation Plan

## Scope

Replace MATLAB `.p` dependencies from HybridDynamicRT with Python-native modules while preserving output compatibility.

Target `.p` functions:

- `fun_hybrid_generate_channel.p`
- `fun_hybrid_Doppler_estimation.p`
- `fun_hybrid_generate_concatenated_Dop.p`
- `fun_hybrid_Ang_estimation.p`
- `fun_hybrid_calculate_reflecting_path_power.p`
- `fun_hybrid_calculate_scattering_path_power.p`

## Priority Order

1. `generate_channel` (core input to Doppler/Angle)
2. `Doppler_estimation`
3. `generate_concatenated_Dop`
4. `Ang_estimation`
5. `calculate_reflecting_path_power`
6. `calculate_scattering_path_power`

## Progress Tracking

- [x] P1: `generate_channel` Python implementation + unit validation
- [x] P2: Doppler map estimation implementation + validation
- [x] P3: Concatenated Doppler metrics implementation + validation
- [ ] P4: Angle estimation implementation + validation
- [ ] P5: Reflecting/scattering power models implementation + validation
- [ ] P6: Full pipeline parity check on Hybrid frame ingest path

## Validation Rule

Each P-step must include:

1. Source-compatible function signature or explicit mapping wrapper.
2. Deterministic validation script under `/Users/seongcheoljeong/Documents/Codex_test/scripts/`.
3. Validation record entry in `/Users/seongcheoljeong/Documents/Codex_test/docs/validation_log.md`.

## Non-goal for this phase

- No `.ffd` coupling before P1-P5 are complete.
- No real-time optimization before functional parity is established.
