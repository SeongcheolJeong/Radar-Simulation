# Targeted Flat-Refine Search Report (Xiangyu Targets, 2026-02-21)

## Inputs

- Cases:
  - `bms1000_512`
  - `bms1000_full897`
  - `cms1000_128`
- Baseline reports:
  - rerun-baseline outputs from `xiangyu_target_batch_v2_rerun_baseline`
- CSV sources:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/experiment_matrix/csv_512/bms1000_path_power_samples_512.csv`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/experiment_matrix/csv_128/cms1000_path_power_samples_128.csv`
- Constrained summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/constrained_refit_drift_search_xiangyu_targets_flat_refine_v2_2026_02_21.json`
- Consistency gate summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/constrained_refit_consistency_gate_xiangyu_targets_flat_refine_v2_2026_02_21.json`

## Run Configuration

- Presets: `flat_fine_a`, `flat_fine_b`, `flat_fine_c`
- Hard limits:
  - `drift_max_pass_rate_drop=0.0`
  - `drift_max_pass_count_drop_ratio=0.0`
  - `drift_max_fail_count_increase_ratio=0.0`
  - `drift_max_metric_drift=0.1`
- Fit-proxy caps:
  - `max_range_exp=1.25`
  - `max_azimuth_power=1.5`
  - `weight=[0.9, 1.1]`
- Candidate coverage guard:
  - `max_no_gain_attempts=8` (full 4-fit evaluation per preset)

## Result Snapshot

- All 3 presets completed with `fit_json_count=4`.
- All 3 presets selected:
  - `selection_mode=baseline_no_fit`
  - recommendation: `fallback_to_baseline_no_fit`
- No eligible fit candidate remained under strict limits.

Per-preset candidate rejection pattern:

- reflection fits: pass/fail degradation limit violations
- scattering fits: pass/fail degradation + metric drift limit violations

## Consistency Gate

- `eligible_preset_count=0`
- `gate_failed=true`
- final decision: `baseline_no_fit`

## Interpretation

Targeted flat-region refinement removed prior candidate truncation inefficiency and confirmed full-candidate evidence.
Under strict non-degradation constraints, Xiangyu 3-case targets still have no adoptable fit-lock candidate; baseline fallback remains the stable decision.
