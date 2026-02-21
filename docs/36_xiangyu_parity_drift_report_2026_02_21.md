# Xiangyu Parity Drift Report (2026-02-21)

## Source

- Drift JSON:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/parity_drift_xiangyu_policy_strict_2026_02_21.json`
- Baseline:
  - `bms1000_512`
- Compared scenarios:
  - `bms1000_897`
  - `cms1000_128`

## Replay Status

All compared runs used policy-governed tuned profiles and strict replay lock:

- `pass_rate = 1.0` for all three scenarios

## Selected Drift Signals (q90, vs baseline)

### `bms1000_897` vs `bms1000_512`

- `rd_shape_nmse`: ratio `1.0338`, delta `+0.011878`
- `ra_shape_nmse`: ratio `1.0942`, delta `+0.021797`
- `rd_peak_power_db_abs_error`: ratio `1.0860`, delta `+0.124199`
- `ra_peak_power_db_abs_error`: ratio `1.0735`, delta `+0.189154`

Interpretation: same-family longer run shows mild drift.

### `cms1000_128` vs `bms1000_512`

- `rd_shape_nmse`: ratio `1.3207`, delta `+0.112568`
- `ra_shape_nmse`: ratio `7.1171`, delta `+1.415688`
- `rd_peak_power_db_abs_error`: ratio `0.7940`, delta `-0.297667`
- `ra_peak_power_db_abs_error`: ratio `0.5343`, delta `-1.198788`

Interpretation: cross-family shift is concentrated in RA shape-type metrics.

## Next Physics Action

Use this drift report as target for path-power/scattering parameter tuning experiments, prioritizing RA shape metrics for cross-family generalization.
