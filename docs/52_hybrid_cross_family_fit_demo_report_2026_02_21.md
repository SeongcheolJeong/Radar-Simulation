# Hybrid Cross-Family Fit Demo Report (2026-02-21)

## Inputs

- Selected reflection fit JSON:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits/path_power_fit_reflection_selected.json`
- Demo output summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/hybrid_cross_family_fit_demo_reflection_2026_02_21.json`

Demo cases:

- `case_a`: baseline demo frames
- `case_b`: same frames with far-target amplitude boosted

## Result Snapshot

- `b_baseline_vs_a_baseline`: pass
- `b_tuned_vs_a_baseline`: fail
- RA improved ratio: `0.0`
- RD improved ratio: `0.0`

Selected metric deltas (`tuned - baseline`):

- `rd_shape_nmse`: `+0.142938`
- `ra_shape_nmse`: `+0.145506`
- `rd_peak_power_db_abs_error`: `+0.860005`
- `ra_peak_power_db_abs_error`: `+0.861951`

## Interpretation

- In this demo setup, selected Xiangyu-label fit did not generalize and increased drift.
- Cross-family tuning objective should include this comparator loop before freezing final fit assets.
