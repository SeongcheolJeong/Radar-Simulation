# Path Power Fit Selection Report (Mixed From A/B, Xiangyu Demo, 2026-02-21)

## Inputs

A/B reports:

- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_lock_ab_comparison_reflection_2026_02_21.json`
- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_lock_ab_comparison_scattering_2026_02_21.json`

Source lock sets:

- RMSE-only: `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits`
- cross-family: `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_cross_family`

## Output

- Mixed lock summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_selection_mixed_from_ab_xiangyu_labels_2026_02_21.json`
- Mixed lock fits:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_reflection_selected.json`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_scattering_selected.json`

## Selection Outcome (`tie_policy=keep_rmse`)

Reflection:

- A/B score tie (`86.268252` vs `86.268252`)
- selected source: `rmse_lock`

Scattering:

- A/B winner: `cross_family_lock` (`347.609311 -> 48.288101`)
- selected source: `cross_family_lock`

## Targeted Mixed-Fit Verification

Comparator reports with mixed lock fits:

- reflection mixed:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/hybrid_cross_family_fit_demo_reflection_mixed_2026_02_21.json`
  - score-equivalent value: `86.268252`
- scattering mixed:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/hybrid_cross_family_fit_demo_scattering_mixed_2026_02_21.json`
  - score-equivalent value: `48.288101`

## Recommendation

Use mixed lock set as next baseline:

- reflection: RMSE lock 유지
- scattering: cross-family lock 채택
