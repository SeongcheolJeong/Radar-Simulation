# Case-Partitioned Fit-Lock Report (Xiangyu Targets, 2026-02-21)

## Inputs

- Case-partitioned summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/case_partitioned_fit_lock_xiangyu_targets_flat_refine_v1_2026_02_21.json`
- Reused global summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_constrained_refit_targets_flat_refine_v2/preset_00_flat_fine_a/fit_lock_search_summary.json`
- Fit pool:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_constrained_refit_targets_flat_refine_v2/preset_00_flat_fine_a/fit_batch/fits/*.json`

Case-family mapping:

- `bms1000_512 -> bms1000`
- `bms1000_full897 -> bms1000`
- `cms1000_128 -> cms1000`

## Strategy Result

- Global stage:
  - `selection_mode=baseline_no_fit`
  - recommendation: `fallback_to_baseline_no_fit`
- Family stage:
  - `bms1000`: `selection_mode=fit`, recommendation `adopt_selected_fit_by_drift_objective`
    - selected: `bms1000_reflection.json`
    - penalties: pass/fail drops `0`, `metric_drift_mean=0.0428`
  - `cms1000`: `selection_mode=baseline_no_fit`

Final:

- `strategy=mixed_family_partitioned_lock`
- `selection_mode=fit_partitioned_with_baseline_fallback`
- selected by family:
  - `bms1000 -> bms1000_reflection.json`
  - `cms1000 -> null (baseline)`

## Interpretation

Global lock remains infeasible, but family-partitioned fallback recovered an adoptable fit for the BMS family without pass/fail degradation.
This establishes a practical next path: apply selective family lock where safe, baseline elsewhere.
