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
- [x] M10.08: Path-power fit cycle orchestration (`baseline->samples->fit->tuned`) + summary automation
- [x] M10.09: Cross-family parity shift evaluator (`baseline/tuned x familyA/familyB`) + Xiangyu report
- [x] M10.10: Path-power fit batch runner (`multi CSV x multi model`) + demo summary
- [x] M10.11: Xiangyu label+ADC -> path_power_samples converter + real 128-frame CSV runs
- [x] M10.12: Xiangyu label-fit experiment matrix runner (`frame-count sweep`) + 128/512 report
- [x] M10.13: Path-power fit selection/lock from experiment summary (`largest_frame_then_rmse`)
- [x] M10.14: Hybrid cross-family fit comparator (`caseA ref`, `caseB baseline/tuned`) + first demo run
- [x] M10.15: Cross-family fit ranking objective (`comparator-based score`) + Xiangyu reflection/scattering ranking reports
- [x] M10.16: Cross-family ranking-based fit lock selection + Xiangyu RMSE-vs-cross-family selection delta report
- [x] M10.17: RMSE-lock vs cross-family-lock A/B comparator replay report (reflection/scattering)
- [x] M10.18: Mixed lock publish from A/B reports (`reflection keep`, `scattering cross-family`) + targeted comparator verification
- [x] M10.19: Measured replay fit-change impact gate (dependency audit) + Xiangyu no-op skip decision
- [x] M10.20: Fit-aware measured pack rebuild path + real-plan replay impact confirmation (`bms1000_run1`)
- [x] M10.21: Fit-aware measured replay batch scaling to target plans + no-gain stop gate execution
- [x] M10.22: Fit-aware replay saturation sanity gate and target-batch risk classification
- [x] M10.23: Current-code baseline rerun gate for fit-aware batch + stale-baseline correction report
- [x] M10.24: Fit-aware replay adoption policy gate (non-degradation + min-improvement) + Xiangyu decision
- [x] M10.25: Fit-lock policy selection with baseline fallback (candidate search on batch summary)
- [x] M10.26: Fit-lock candidate search orchestrator with headroom short-circuit (efficiency gate)
- [x] M10.27: Saturated-baseline drift objective and exploratory fit ranking path
- [x] M10.28: Constrained refit loop (preset grids) + drift-objective search ranking
- [x] M10.29: Multi-case constrained-refit consistency gate + Xiangyu target decision
- [x] M10.30: Targeted flat-refine constrained search + full-candidate evidence pass

## Iteration Rule (One-by-One Verification)

Each milestone is accepted only if:

1. Contract is documented (`docs/*.md`)
2. Reproducible validation command exists (`scripts/*.py`)
3. Pass/fail criteria are explicit
4. Result is logged in `docs/validation_log.md`

## Immediate Next Step

Start M10.31: evaluate case-partitioned fit-lock strategy (global lock -> per-family lock fallback).

## M10.19 Decision Gate

Accept M10.19 only if at least one holds:

1. mixed lock improves replay lock quality vs prior strict-tuned baseline
2. mixed lock keeps quality within tolerance while reducing cross-family drift score

Stop and re-plan M10.19 when:

- two attempts show no improvement/no new failure signal
- measured replay inputs are insufficient to evaluate lock quality

M10.19 outcome (2026-02-21):

- measured replay plans show no dependency on selected fit JSON assets
- rerun skipped as no-op per workflow Value-Gate/Repetition rules

M10.20 outcome (2026-02-21):

- fit-aware pack rebuild path implemented from existing packs
- representative real plan (`bms1000_run1`) replay became fit-sensitive (`pass_count 1 -> 12`)

M10.21 outcome (2026-02-21):

- fit-aware measured replay batch runner executed on target plans (`bms1000_512`, `bms1000_full897`, `cms1000_128`)
- all 3 cases improved over baseline (`improved_case_count=3`)
- stop gate condition (`max_no_gain_attempts=2`) remained armed; no case hit no-gain streak in this run
- superseded by M10.23 due stale historical baseline reports

M10.22 outcome (2026-02-21):

- saturation sanity gate added for fit-aware replay batch summaries
- Xiangyu target batch analysis flagged `2/3` saturated cases (`bms1000_512`, `bms1000_full897`)
- recommendation emitted: `proxy_strength_review_required`
- superseded by M10.23 rerun-baseline analysis

M10.23 outcome (2026-02-21):

- fit-aware batch runner updated with `baseline-mode=rerun|provided` (default `rerun`) to remove stale baseline dependency
- rerun-baseline Xiangyu target batch result: `improved_case_count=0` (`3/3` no-gain, stop gate triggered)
- rerun-baseline saturation gate result: `saturated_case_count=0`, recommendation `proxy_strength_within_expected_range`
- key conclusion corrected: current issue is not saturation uplift but fit-aware degradation vs current baseline

M10.24 outcome (2026-02-21):

- policy gate added to formalize adoption decision using rerun-baseline batch summary
- Xiangyu rerun-baseline policy result: `degrade_only_case_count=3`, `improved_case_count=0`
- recommendation fixed as `reject_fit_lock_due_to_degradation`

M10.25 outcome (2026-02-21):

- fit-lock selector added to rank/accept/reject fit candidates from batch summary
- Xiangyu rerun-baseline selection result: no eligible fit candidate
- deterministic fallback selected: `baseline_no_fit`

M10.26 outcome (2026-02-21):

- fit-lock search orchestrator added (`baseline -> feasibility -> batch/policy/selection`)
- Xiangyu rerun-baseline search with 6 fit candidates detected `headroom=0`
- search short-circuited before fit-aware batch rerun and emitted fallback `baseline_no_fit`

M10.27 outcome (2026-02-21):

- drift-objective fit selector implemented for saturated baseline use-cases
- Xiangyu 3-case rerun-baseline drift ranking selected `reflection` as least-distorting candidate
- recommendation explicitly marked exploratory because pass/fail degradation still exists
- search orchestrator supports `--objective-mode drift` for non-short-circuited exploratory analysis

M10.28 outcome (2026-02-21):

- constrained refit loop implemented (`run_path_power_fit_batch -> run_measured_replay_fit_lock_search[drift]`) with preset-wise ranking
- default `flat` preset grid corrected to valid positive range exponents (`range_power_exponent > 0`)
- synthetic end-to-end validation added (`validate_run_constrained_refit_drift_search.py`)
- Xiangyu `bms1000_512` 3-preset probe selected `flat` as best (`adopt_selected_fit_by_drift_objective`, score `0.0512`)

M10.29 outcome (2026-02-21):

- multi-case constrained search executed on Xiangyu targets (`bms1000_512`, `bms1000_full897`, `cms1000_128`)
- consistency gate added to convert preset-search results into deterministic adopt/fallback decision
- gate diagnostics showed all presets violate non-degradation constraints on the 3-case set
- final decision fixed as fallback `baseline_no_fit`

M10.30 outcome (2026-02-21):

- constrained search upgraded with drift/fit-proxy pass-through and `max-no-gain-attempts` control
- targeted flat-refine sweep executed (`flat_fine_a/b/c`) under strict non-degradation limits
- no-gain truncation inefficiency removed (all 4 fit candidates evaluated per preset)
- all presets still fell back to `baseline_no_fit`; strict multi-case adoption remained unavailable
