# Path Power Fit Batch Demo Report (2026-02-21)

## Source

- Summary JSON:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/path_power_fit_batch_demo_2026_02_21.json`
- Fit JSON directory:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cycle_demo/fit_batch_run/fits`

## Input Cases

- `demoA`: `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cycle_demo/path_power_samples.csv`
- `demoB`: `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_cycle_demo/cycle_run/path_power_samples.csv`

Models:

- `reflection`
- `scattering`

## Result Snapshot

- run count: `4` (`2 cases x 2 models`)

Best reflection fit:

- case: `demoA`
- rmse_log: `0.246728`
- params:
  - `range_power_exponent=2.5`
  - `gain_scale=9595214.6037`

Best scattering fit:

- case: `demoA`
- rmse_log: `0.087911`
- params:
  - `range_power_exponent=2.5`
  - `elevation_power=0.5`
  - `azimuth_mix=0.0`
  - `azimuth_power=2.0`
  - `gain_scale=187455398.4451`

## Note

This is a workflow validation report using path-list-derived demo CSVs, not real measured calibration CSVs.
