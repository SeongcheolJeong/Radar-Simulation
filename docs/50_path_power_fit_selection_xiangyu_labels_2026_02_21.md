# Path Power Fit Selection Report (Xiangyu Labels, 2026-02-21)

## Inputs

- Experiment summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/xiangyu_label_fit_experiment_128_512_2026_02_21.json`
- Strategy:
  - `largest_frame_then_rmse`

## Selected Outputs

- Summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_selection_xiangyu_labels_2026_02_21.json`
- Locked fit JSONs:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits/path_power_fit_reflection_selected.json`
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits/path_power_fit_scattering_selected.json`

## Selection Snapshot

Reflection:

- selected case: `cms1000`
- selected frame-count: `512`
- best params:
  - `range_power_exponent=5.0`
  - `gain_scale=10553699891.68124`

Scattering:

- selected case: `cms1000`
- selected frame-count: `512`
- best params:
  - `range_power_exponent=5.0`
  - `elevation_power=0.5`
  - `azimuth_mix=0.0`
  - `azimuth_power=4.0`
  - `gain_scale=14965909323.830236`

## Note

Selected JSONs are now ready to be used as fixed fit inputs for subsequent tuned ingest experiments.
