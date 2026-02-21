# Path Power Fit Cross-Family Ranking Report (2026-02-21)

## Inputs

- Experiment matrix summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/xiangyu_label_fit_experiment_128_512_2026_02_21.json`
- Case-A / Case-B demo data:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_a/frames`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cross_family_demo/case_b/frames`

## Outputs

- Reflection ranking summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_cross_family_ranking_reflection_2026_02_21.json`
- Scattering ranking summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_cross_family_ranking_scattering_2026_02_21.json`

## Result Snapshot

Reflection:

- candidate count: `4` (ok: `4`)
- best fit:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/experiment_matrix/fit_128/fits/cms1000_reflection.json`
- best score: `86.268252`
- best tuned pass: `false`

Scattering:

- candidate count: `4` (ok: `4`)
- best fit:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/experiment_matrix/fit_128/fits/bms1000_scattering.json`
- best score: `48.288101`
- best tuned pass: `false`

## Notes

- Ranking now supports dataset-specific frame naming via prefix/scale overrides.
- In this demo, both models still fail tuned pass threshold; ranking currently finds "least drift increase" rather than absolute pass.
