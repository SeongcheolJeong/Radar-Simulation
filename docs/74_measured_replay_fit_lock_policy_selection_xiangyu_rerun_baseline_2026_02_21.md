# Measured Replay Fit-Lock Selection Report (Xiangyu Rerun Baseline, 2026-02-21)

## Input

- Rerun-baseline fit-aware batch summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_measured_replay_batch_xiangyu_targets_rerun_baseline_2026_02_21.json`
- Selection output:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/measured_replay_fit_lock_policy_selection_xiangyu_rerun_baseline_2026_02_21.json`

Policy:

- `max_pass_rate_drop=0.0`
- `max_pass_count_drop=0`
- `max_fail_count_increase=0`
- `min_improved_cases=1`
- `require_full_case_coverage=true`

## Result Snapshot

- fit candidates evaluated: `2`
- eligible candidates: `0`
- selection mode: `baseline_no_fit`
- recommendation: `fallback_to_baseline_no_fit`

Candidate aggregates:

- `path_power_fit_scattering_selected.json`:
  - `non_degrading_case_count=0/3`
  - `improved_case_count=0/3`
  - rejected: `degradation_detected`, `insufficient_improved_cases`
- `path_power_fit_reflection_selected.json`:
  - `non_degrading_case_count=0/3`
  - `improved_case_count=0/3`
  - rejected: `degradation_detected`, `insufficient_improved_cases`

## Interpretation

For measured replay lock adoption, current mixed fit set is rejected and fallback to baseline no-fit is selected.
This closes M10.25 with a deterministic fallback decision path.
