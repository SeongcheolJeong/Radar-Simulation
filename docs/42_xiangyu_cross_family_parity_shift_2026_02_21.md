# Xiangyu Cross-Family Parity Shift Report (2026-02-21)

## Source

- Report JSON:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/cross_family_parity_shift_xiangyu_2026_02_21.json`

Families used:

- Family A: `bms1000_512`
- Family B: `cms1000_128`

Compared conditions:

- baseline replay outputs
- tuned replay outputs (`tuned_strict_v2` for bms, `tuned_strict` for cms)

## Result Snapshot

### Pass-rate alignment

- baseline cross-family pass-rate gap (abs): `0.083984`
- tuned cross-family pass-rate gap (abs): `0.000000`
- reduction: `0.083984`

### Metric gap reduction (q50/q90/q99)

- `ra_shape_nmse`: reduction `0.0 / 0.0 / 0.0`
- `rd_shape_nmse`: reduction `0.0 / 0.0 / 0.0`
- `ra_peak_power_db_abs_error`: reduction `0.0 / 0.0 / 0.0`
- `rd_peak_power_db_abs_error`: reduction `0.0 / 0.0 / 0.0`

## Interpretation

- In this replay set, tuned profile lock improved pass/fail consistency across families.
- But cross-family metric quantile gaps did not change.
- Therefore, this result should be interpreted as policy/lock convergence, not confirmed physics-shape improvement.

## Next M10.1 Action

Run the same cross-family evaluator using tuned outputs generated from measured path-power fit JSONs built from real calibration CSVs.
