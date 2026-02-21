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
- [x] M6: P-code replacement wave-2 (`path power` models and calibration)
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
- [x] M8.26: Measured replay execution orchestration (multi-pack batch)
- [x] M8.27: Measured replay plan auto-builder (pack discovery)
- [x] M8.28: Per-pack replay manifest auto-builder
- [x] M8.29: Mock measured packs generator for no-data bootstrap
- [x] M8.3: Measured moving-target replay execution and profile lock finalization
- [x] M9.0: Public dataset conversion scaffolding (`MAT->ADC NPZ->pack`)
- [x] M9.05: One-command onboarding pipeline (`input->pack->plan->replay`)
- [x] M9.1: First public dataset schema lock and real subset conversion run
- [x] M10.0: Path-power tuning tooling + parity drift quantification baseline
- [x] M10.05: Path-power fit ingest integration (`--path-power-fit-json`) + CLI validation

## Iteration Rule (One-by-One Verification)

Each milestone is accepted only if:

1. Contract is documented (`docs/*.md`)
2. Reproducible validation command exists (`scripts/*.py`)
3. Pass/fail criteria are explicit
4. Result is logged in `docs/validation_log.md`

## Immediate Next Step

Start M10.1: run measured path-power parameter fitting experiments (reflection/scattering) using real calibration CSVs and evaluate whether RA drift (cross-family) is reduced.
