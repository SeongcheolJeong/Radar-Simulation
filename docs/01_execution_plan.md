# Execution Plan

## Goal

Build an AVX-like offline radar simulator for FMCW + TDM-MIMO that can emit:

- propagation path list
- raw ADC cube

## Milestones

- [x] M0: Paper-to-code traceability matrix
- [x] M1: Documentation baseline and contracts
- [x] M2: Minimal path-to-ADC synthesis core
- [x] M3: Deterministic validation script (3 scenarios)
- [x] M3.5: Reference adapter scaffolding + smoke validation
- [x] M4: P-code replacement wave-1 (`generate_channel`, `Doppler`, `concatenated Dop`, `Angle`)
- [x] M5: RT adapter base (HybridDynamicRT frame ingestion, first version)
- [x] M5.5: Hybrid ingest pipeline and canonical output writer
- [ ] M6: P-code replacement wave-2 (`path power` models and calibration)
- [x] M7: `.ffd` parser + interpolation
- [x] M7.5: Jones polarization flow through path/antenna/synth
- [x] M7.6: RD/RA parity metrics comparator baseline
- [x] M7.7: Global Jones calibration bootstrap (LS fitter + ingest hook)
- [x] M7.8: Calibration sample builder (`path_list + adc + ffd -> calibration_samples.npz`)
- [x] M7.9: Measured CSV converter (`measurement.csv -> calibration_samples.npz`)
- [x] M7.10: Scenario profile lock (`global_jones + parity thresholds + evaluator`)
- [x] M8: Motion compensation baseline for TDM virtual array
- [x] M8.1: Motion compensation tuning workflow and profile-default lock
- [x] M8.2: Moving-target replay batch automation and reporting
- [x] M8.25: Replay-based scenario profile lock finalization tooling
- [ ] M8.3: Measured moving-target replay execution and profile lock finalization

## Iteration Rule (One-by-One Verification)

Each milestone is accepted only if:

1. Contract is documented (`docs/*.md`)
2. Reproducible validation command exists (`scripts/*.py`)
3. Pass/fail criteria are explicit
4. Result is logged in `docs/validation_log.md`

## Immediate Next Step

Execute measured replay datasets through batch runner, run lock finalization CLI, and version locked per-scenario profiles.
