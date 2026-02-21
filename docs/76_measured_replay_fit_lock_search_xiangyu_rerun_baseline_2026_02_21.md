# Measured Replay Fit-Lock Search Report (Xiangyu Rerun Baseline, 2026-02-21)

## Inputs

- Cases:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/packs/pack_xiangyu_2019_04_09_bms1000_v1_512`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run3_full897/packs/pack_xiangyu_2019_04_09_bms1000_v1_full897`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/packs/pack_xiangyu_2019_04_09_cms1000_v1_128`
- Candidate fit pools:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_cross_family`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed`
- Output summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/measured_replay_fit_lock_search_xiangyu_rerun_baseline_2026_02_21.json`

## Result Snapshot

- `fit_json_count=6`
- `baseline_mode=rerun`
- baseline headroom:
  - `cases_with_improvement_headroom=0`
  - each case baseline replay was `pass_rate=1.0`
- `short_circuit=true`
- short-circuit reason: `insufficient_improvement_headroom`
- final selection:
  - `selection_mode=baseline_no_fit`
  - recommendation: `fallback_to_baseline_no_fit`

## Efficiency Impact

Because no case had improvement headroom, fit-aware batch replay was skipped.
This avoids repeated expensive no-value runs while preserving deterministic lock decision output.
