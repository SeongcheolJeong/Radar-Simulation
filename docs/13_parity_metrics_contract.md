# Parity Metrics Contract (RD/RA)

## Goal

Provide a deterministic comparator for `hybrid_estimation.npz` outputs so we can gate regressions against reference snapshots.

## Inputs

- Reference: `hybrid_estimation.npz`
- Candidate: `hybrid_estimation.npz`

Required arrays:

- RD map: `fx_dop_win` (fallback `fx_dop`)
- RA map: `fx_ang`

Shape rule:

- RD and RA shapes must match between reference and candidate.

## Metrics

RD metrics:

- `rd_peak_doppler_bin_abs_error`
- `rd_peak_range_bin_abs_error`
- `rd_peak_power_db_abs_error`
- `rd_centroid_doppler_bin_abs_error`
- `rd_centroid_range_bin_abs_error`
- `rd_spread_doppler_rel_error`
- `rd_spread_range_rel_error`
- `rd_shape_nmse`

RA metrics:

- `ra_peak_angle_bin_abs_error`
- `ra_peak_range_bin_abs_error`
- `ra_peak_power_db_abs_error`
- `ra_centroid_angle_bin_abs_error`
- `ra_centroid_range_bin_abs_error`
- `ra_spread_angle_rel_error`
- `ra_spread_range_rel_error`
- `ra_shape_nmse`

## Default Thresholds

Implemented in:

- `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/parity.py` (`DEFAULT_PARITY_THRESHOLDS`)

Each threshold key ends with `_max`. Any metric over that limit is a parity failure.

## CLI

Comparator script:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/compare_hybrid_estimation_parity.py \
  --reference-npz /path/to/reference_hybrid_estimation.npz \
  --candidate-npz /path/to/candidate_hybrid_estimation.npz \
  --output-json /path/to/parity_report.json
```

Validation script:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_parity_metrics_contract.py
```

## Next Step

Use measured scenarios to tune threshold values per use case (static target, constant velocity, multipath).

