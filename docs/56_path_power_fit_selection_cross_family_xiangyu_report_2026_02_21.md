# Path Power Fit Selection Report (Cross-Family, Xiangyu Labels, 2026-02-21)

## Inputs

- Reflection ranking summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_cross_family_ranking_reflection_2026_02_21.json`
- Scattering ranking summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_cross_family_ranking_scattering_2026_02_21.json`
- RMSE-only previous selection summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_selection_xiangyu_labels_2026_02_21.json`

## Outputs

- Cross-family selection summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_selection_cross_family_xiangyu_labels_2026_02_21.json`
- Locked fits:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_cross_family/path_power_fit_reflection_selected.json`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_cross_family/path_power_fit_scattering_selected.json`

## Selection Snapshot

Reflection selected source fit:

- `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/experiment_matrix/fit_128/fits/cms1000_reflection.json`
- score: `86.268252`
- tuned pass: `false`

Scattering selected source fit:

- `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/experiment_matrix/fit_128/fits/bms1000_scattering.json`
- score: `48.288101`
- tuned pass: `false`

## RMSE-Only vs Cross-Family Selection Change

Reflection:

- RMSE-only: `fit_512/cms1000_reflection.json`
- cross-family: `fit_128/cms1000_reflection.json`
- changed: `true`

Scattering:

- RMSE-only: `fit_512/cms1000_scattering.json`
- cross-family: `fit_128/bms1000_scattering.json`
- changed: `true`

## Note

Cross-family objective changed selected assets for both models. Next step is replay/ingest comparison with these newly locked fits vs RMSE-only locked fits.
