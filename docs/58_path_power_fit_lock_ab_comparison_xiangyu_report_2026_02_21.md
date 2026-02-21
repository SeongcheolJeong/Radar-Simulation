# Path Power Fit Lock A/B Comparison Report (Xiangyu Demo, 2026-02-21)

## Inputs

RMSE-only locked fits:

- `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits/path_power_fit_reflection_selected.json`
- `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits/path_power_fit_scattering_selected.json`

Cross-family locked fits:

- `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_cross_family/path_power_fit_reflection_selected.json`
- `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_cross_family/path_power_fit_scattering_selected.json`

A/B summaries:

- Reflection:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_lock_ab_comparison_reflection_2026_02_21.json`
- Scattering:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_lock_ab_comparison_scattering_2026_02_21.json`

## Result Snapshot

Reflection:

- RMSE score: `86.268252`
- Cross-family score: `86.268252`
- winner: `cross_family_lock` (`score_tie_prefers_cross_family`, tie=true)
- tuned metric deltas (cross - rmse): RA mean `0.0`, RD mean `0.0`

Scattering:

- RMSE score: `347.609311`
- Cross-family score: `48.288101`
- winner: `cross_family_lock` (`lower_score`, tie=false)
- tuned metric deltas (cross - rmse):
  - RA mean: `-149.697714` (improved)
  - RD mean: `+0.074218` (worsened)

## Interpretation

- Reflection lock change has no effect in this demo setup (same comparator result).
- Scattering lock change strongly favors cross-family lock by score.
- Mixed policy candidate for next step:
  - reflection: keep existing lock (either is equivalent in this demo)
  - scattering: adopt cross-family lock
