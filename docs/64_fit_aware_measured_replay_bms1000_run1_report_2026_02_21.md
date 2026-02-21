# Fit-Aware Measured Replay Report (BMS1000 Run1, 2026-02-21)

## Why This Step

M10.19 showed current measured replay plans were no-op for fit lock changes.
This step introduces fit-aware pack rebuild and verifies measured replay impact on a representative real plan.

## Inputs

- Source pack:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run1/packs/pack_xiangyu_2019_04_09_bms1000_v1`
- Fit JSON (mixed lock, scattering):
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed/path_power_fit_scattering_selected.json`

## Outputs

- Fit-aware pack summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_bms1000_run1_scattering_mixed/fit_aware_pack_summary.json`
- Fit-aware measured replay summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/fit_aware_runs/xiangyu_bms1000_run1_scattering_mixed/measured_replay_summary.json`
- Baseline vs fit-aware comparison:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/measured_replay_fit_aware_bms1000_run1_compare_2026_02_21.json`
- Fit-dependency impact check on fit-aware plan:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/measured_replay_fit_change_impact_fit_aware_bms1000_run1_2026_02_21.json`

## Result Snapshot

Baseline replay (`bms1000_run1`):

- candidates: `128`
- pass: `1`
- fail: `127`
- pass_rate: `0.0078125`

Fit-aware replay (same source ADC list):

- candidates: `128`
- pass: `12`
- fail: `116`
- pass_rate: `0.09375`

Delta (fit-aware - baseline):

- pass_count: `+11`
- pass_rate: `+0.0859375`
- candidate pass-status changed: `11`

Impact gate on fit-aware plan:

- `predicted_noop_all_plans=false`
- recommendation: `rerun_required_for_impacted_plans`

## Interpretation

Measured replay can be made fit-sensitive when candidate generation is rebuilt through fit-aware proxy path.
This resolves the M10.19 no-op condition for affected plans.
