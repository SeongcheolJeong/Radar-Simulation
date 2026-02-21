# Xiangyu Label Fit Experiment Report (2026-02-21)

## Summary JSON

- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/xiangyu_label_fit_experiment_128_512_2026_02_21.json`

## Experiment Matrix

Cases:

- `bms1000` (`2019_04_09_bms1000`)
- `cms1000` (`2019_04_09_cms1000`)

Frame counts:

- `128`
- `512`

Models:

- `reflection`
- `scattering`

## Result Snapshot

### frame_count = 128

- selected rows:
  - `bms1000: 128`
  - `cms1000: 127`
- best reflection case: `bms1000`
  - `range_power_exponent=2.5`
- best scattering case: `bms1000`
  - `range_power_exponent=2.5`, `elevation_power=0.5`, `azimuth_mix=0.2`, `azimuth_power=4.0`

### frame_count = 512

- selected rows:
  - `bms1000: 512`
  - `cms1000: 511`
- best reflection case: `cms1000`
  - `range_power_exponent=5.0`
- best scattering case: `cms1000`
  - `range_power_exponent=5.0`, `elevation_power=0.5`, `azimuth_mix=0.0`, `azimuth_power=4.0`

## Interpretation

- Label-derived fit preference shifts with dataset size (128 vs 512).
- This indicates parameter stability check is required before freezing fit JSON for tuned ingest/replay experiments.
