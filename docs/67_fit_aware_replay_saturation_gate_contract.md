# Fit-Aware Replay Saturation Gate Contract

## Goal

Detect over-strong fit-aware proxy behavior by checking whether replay quality jumps are unrealistically saturated across many candidates.

## Core CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/analyze_fit_aware_replay_saturation.py \
  --batch-summary-json /path/to/fit_aware_measured_replay_batch_summary.json \
  --output-json /path/to/fit_aware_replay_saturation_summary.json \
  --min-baseline-candidate-count 64 \
  --high-pass-rate-threshold 0.98 \
  --large-pass-rate-delta-threshold 0.5 \
  --pass-status-change-ratio-threshold 0.8 \
  --max-allowed-saturated-cases 0
```

## Saturation Criteria (per case)

Case is marked saturated only when all are true:

- baseline candidate count >= `min_baseline_candidate_count`
- best fit-aware pass rate >= `high_pass_rate_threshold`
- pass-rate delta >= `large_pass_rate_delta_threshold`
- changed pass-status ratio >= `pass_status_change_ratio_threshold`

## Output

Summary JSON contains:

- `saturated_case_count`
- `gate_failed`
- `recommendation`
- per-case metrics and criteria flags

Recommendation:

- `proxy_strength_review_required` when saturated case count exceeds allowed limit
- `proxy_strength_within_expected_range` otherwise

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_fit_aware_replay_saturation.py
```

Validation checks:

- saturated vs non-saturated case classification
- gate failure when allowed saturated cases is `0`
- gate pass when allowed saturated cases is relaxed to `1`
