# Fit-Aware Measured Replay Batch Report (Xiangyu Targets, 2026-02-21)

Superseded note (2026-02-21):

- This report used historical baseline replay reports generated before current replay execution updates.
- Use `/Users/seongcheoljeong/Documents/Codex_test/docs/69_fit_aware_measured_replay_batch_xiangyu_targets_rerun_baseline_2026_02_21.md` as the corrected reference.

## Inputs

- Source packs:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/packs/pack_xiangyu_2019_04_09_bms1000_v1_512`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run3_full897/packs/pack_xiangyu_2019_04_09_bms1000_v1_full897`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/packs/pack_xiangyu_2019_04_09_cms1000_v1_128`
- Fit order:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_scattering_selected.json`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_reflection_selected.json`
- Output summary JSON:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_measured_replay_batch_xiangyu_targets_2026_02_21.json`

## Batch Snapshot

- `case_count=3`
- `improved_case_count=3`
- `max_no_gain_attempts=2`
- all cases ended by `stop_reason=fit_list_exhausted` (no no-gain streak)

## Per-Case Best Attempt Delta (vs baseline)

- `bms1000_512`:
  - baseline pass/fail/rate: `1/511/0.001953125`
  - best fit: `scattering_selected`
  - fit-aware pass/fail/rate: `512/0/1.0`
  - delta: `pass_count +511`, `pass_rate +0.998046875`
- `bms1000_full897`:
  - baseline pass/fail/rate: `1/896/0.0011148272`
  - best fit: `scattering_selected`
  - fit-aware pass/fail/rate: `897/0/1.0`
  - delta: `pass_count +896`, `pass_rate +0.9988851728`
- `cms1000_128`:
  - baseline pass/fail/rate: `11/117/0.0859375`
  - best fit: `scattering_selected`
  - fit-aware pass/fail/rate: `29/99/0.2265625`
  - delta: `pass_count +18`, `pass_rate +0.140625`

## Interpretation

- Fit-aware rebuild path scales to multiple real target plans and is no longer a single-plan check.
- Replay output is clearly fit-sensitive for these plans, with largest uplift on BMS1000 packs.
- Since uplift is very large in two cases, next step should include a saturation sanity gate to confirm proxy strength is physically acceptable before default rollout.
