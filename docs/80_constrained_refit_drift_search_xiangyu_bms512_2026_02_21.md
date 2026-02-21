# Constrained Refit Drift Search Report (Xiangyu BMS1000-512, 2026-02-21)

## Inputs

- Case:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/packs/pack_xiangyu_2019_04_09_bms1000_v1_512`
- Baseline replay report:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_target_batch_v2_rerun_baseline/case_00_bms1000_512/baseline_current/measured_replay_outputs/pack_xiangyu_2019_04_09_bms1000_v1_512/replay_report.json`
- Path-power samples CSV:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/experiment_matrix/csv_512/bms1000_path_power_samples_512.csv`
- Constrained refit summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/constrained_refit_drift_search_xiangyu_bms512_all_presets_2026_02_21.json`

## Preset Ranking Snapshot

- `flat`:
  - recommendation: `adopt_selected_fit_by_drift_objective`
  - selected aggregate score: `0.0512`
  - selected fit: `bms1000_512_reflection.json`
- `balanced`:
  - recommendation: `exploratory_fit_candidate_selected_by_drift`
  - selected aggregate score: `0.3435`
- `steep`:
  - recommendation: `exploratory_fit_candidate_selected_by_drift`
  - selected aggregate score: `132.6327`

Best preset: `flat`.

## Policy vs Drift Objective

`flat` preset search summary:

- policy gate: `hold_fit_lock_no_material_gain` (gate failed)
- drift selector recommendation: `adopt_selected_fit_by_drift_objective`
- degradation penalties: all zero
  - `pass_rate_drop=0.0`
  - `pass_count_drop_ratio=0.0`
  - `fail_count_increase_ratio=0.0`
- residual metric drift:
  - `metric_drift_mean=0.0512`

## Interpretation

On this single-case constrained probe, low-exponent (`flat`) refit candidates avoided pass/fail degradation and minimized drift score, while steeper presets introduced larger degradation penalties.
This closes M10.28 for the constrained-loop mechanism and provides a concrete preset baseline for next multi-case expansion.
