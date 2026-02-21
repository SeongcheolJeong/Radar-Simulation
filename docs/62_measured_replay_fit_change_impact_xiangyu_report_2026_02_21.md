# Measured Replay Fit-Change Impact Report (Xiangyu, 2026-02-21)

## Inputs

Measured replay plans:

- `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run1/measured_replay_plan.json`
- `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run2_512/measured_replay_plan.json`
- `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run3_full897/measured_replay_plan.json`
- `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_cms1000_run1_128/measured_replay_plan.json`

Fit lock sets checked:

- `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits`
- `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_cross_family`
- `/Users/seongcheoljeong/Documents/Codex_test/data/public/path_power_from_xiangyu_labels/selected_fits_mixed`

Output JSON:

- `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/measured_replay_fit_change_impact_xiangyu_2026_02_21.json`

## Result Snapshot

- plan count: `4`
- impacted plan count: `0`
- predicted noop all plans: `true`
- recommendation: `skip_measured_replay_rerun_due_to_no_fit_dependency`

Per plan candidate counts:

- bms1000_run1: `128`
- bms1000_run2_512: `512`
- bms1000_run3_full897: `897`
- cms1000_run1_128: `128`

All packs had:

- `fit_dependency_detected=false`
- `evidence_count=0`

## Interpretation

Changing selected fit JSON assets does not affect current measured replay pipeline inputs (replay manifests, scenario profiles, candidate estimation NPZs) for these plans.

According to Value-Gate/Repetition rules, rerunning measured replay here is skipped as no-op.
