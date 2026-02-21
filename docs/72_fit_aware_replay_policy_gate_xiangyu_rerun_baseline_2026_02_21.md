# Fit-Aware Replay Policy Gate Report (Xiangyu Rerun Baseline, 2026-02-21)

## Inputs

- Batch summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_measured_replay_batch_xiangyu_targets_rerun_baseline_2026_02_21.json`
- Policy gate output:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_replay_policy_gate_xiangyu_rerun_baseline_2026_02_21.json`

Policy used:

- `require_non_degradation_all_cases=true`
- `max_pass_rate_drop=0.0`
- `max_pass_count_drop=0`
- `max_fail_count_increase=0`
- `min_improved_cases=1`

## Result Snapshot

- `case_count=3`
- `non_degrading_case_count=0`
- `degrade_only_case_count=3`
- `improved_case_count=0`
- `gate_failed=true`
- recommendation: `reject_fit_lock_due_to_degradation`

## Interpretation

Under current-code rerun baseline, both selected mixed fits violate non-degradation policy on all target plans.
Current mixed fit lock should be rejected for measured replay adoption.
