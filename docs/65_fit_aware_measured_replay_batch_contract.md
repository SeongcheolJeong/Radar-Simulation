# Fit-Aware Measured Replay Batch Contract

## Goal

Scale fit-aware measured replay evaluation across multiple target packs with ordered fit attempts and an early stop gate for repeated no-gain results.

## Core CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_fit_aware_measured_replay_batch.py \
  --case caseA=/path/to/source_pack_root \
  --case caseB=/path/to/source_pack_root::/path/to/baseline_replay_report.json \
  --fit-json /path/to/path_power_fit_a.json \
  --fit-json /path/to/path_power_fit_b.json \
  --max-no-gain-attempts 2 \
  --allow-unlocked \
  --output-root /path/to/fit_aware_batch_run \
  --output-summary-json /path/to/fit_aware_batch_summary.json
```

## Case Input Rule

- `label=source_pack_root`
- `label=source_pack_root::baseline_replay_report_json`

If baseline replay report is omitted, script auto-resolves:

- `<run_root>/measured_replay_outputs/<pack_name>/replay_report.json`

## Behavior

- for each fit attempt:
  - rebuild fit-aware pack from source ADC list
  - build measured replay plan
  - run measured replay
  - compare replay summary vs baseline (`pass_count`, `pass_rate`)
- gain rule:
  - gain if `pass_count_delta > 0`, or tie-break by `pass_rate_delta > 0`
- stop rule:
  - stop case when `consecutive_no_gain >= max_no_gain_attempts`
- output summary includes:
  - per-case baseline summary
  - per-attempt replay summary and deltas
  - candidate pass-status changed count
  - best attempt and stop reason

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_fit_aware_measured_replay_batch.py
```

Validation checks:

- stop-gate triggers at configured no-gain threshold
- stop reason is `max_no_gain_reached`
- summary schema fields (`case_count`, `fit_attempt_count`) are populated
