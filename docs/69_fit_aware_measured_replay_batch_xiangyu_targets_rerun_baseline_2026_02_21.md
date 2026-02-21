# Fit-Aware Measured Replay Batch Report (Xiangyu Targets, Rerun Baseline, 2026-02-21)

## Why This Rerun

Previous fit-aware batch comparison used historical baseline replay reports.
To remove version skew, baseline replay was re-run with current code (`baseline-mode=rerun`) before fit attempts.

## Inputs

- Source packs:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/packs/pack_xiangyu_2019_04_09_bms1000_v1_512`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run3_full897/packs/pack_xiangyu_2019_04_09_bms1000_v1_full897`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/packs/pack_xiangyu_2019_04_09_cms1000_v1_128`
- Fit order:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_scattering_selected.json`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_reflection_selected.json`
- Output summary JSON:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_measured_replay_batch_xiangyu_targets_rerun_baseline_2026_02_21.json`

## Batch Snapshot

- `baseline_mode=rerun`
- `case_count=3`
- `improved_case_count=0`
- all cases hit `stop_reason=max_no_gain_reached` after 2 attempts

## Per-Case Best Attempt Delta (vs current baseline)

- `bms1000_512`:
  - baseline pass/fail/rate: `512/0/1.0`
  - best fit-aware pass/fail/rate: `0/512/0.0`
  - delta: `pass_count -512`, `pass_rate -1.0`
- `bms1000_full897`:
  - baseline pass/fail/rate: `897/0/1.0`
  - best fit-aware pass/fail/rate: `27/870/0.0301003344`
  - delta: `pass_count -870`, `pass_rate -0.9698996656`
- `cms1000_128`:
  - baseline pass/fail/rate: `128/0/1.0`
  - best fit-aware pass/fail/rate: `0/128/0.0`
  - delta: `pass_count -128`, `pass_rate -1.0`

## Interpretation

- Under current-code baseline replay, fit-aware rebuild is not improving target plans.
- Existing mixed fit lock should not be promoted for measured replay optimization until objective/threshold policy is redefined.
