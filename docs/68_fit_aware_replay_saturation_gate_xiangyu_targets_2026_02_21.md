# Fit-Aware Replay Saturation Gate Report (Xiangyu Targets, 2026-02-21)

## Input

- Batch summary:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_measured_replay_batch_xiangyu_targets_2026_02_21.json`
- Saturation gate output:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/reports/fit_aware_replay_saturation_gate_xiangyu_targets_2026_02_21.json`

## Gate Configuration

- `min_baseline_candidate_count=64`
- `high_pass_rate_threshold=0.98`
- `large_pass_rate_delta_threshold=0.5`
- `pass_status_change_ratio_threshold=0.8`
- `max_allowed_saturated_cases=0`

## Result Snapshot

- `case_count=3`
- `saturated_case_count=2`
- `gate_failed=true`
- recommendation: `proxy_strength_review_required`

Saturated cases:

- `bms1000_512`
- `bms1000_full897`

Non-saturated:

- `cms1000_128`

## Interpretation

The fit-aware proxy currently produces saturation-level improvements on two large BMS1000 target plans.
Before adopting this fit-aware path as a default workflow, proxy-strength cap/tuning should be added and replay should be re-evaluated.
