# Measured Replay Execution Contract

## Goal

Execute multiple measured scenario packs in one command:

1. run replay parity batch
2. finalize scenario profile lock
3. emit per-pack artifacts and an aggregate summary

## Plan JSON

Root can be object with `packs` or list directly.

Each pack:

- `pack_id`
- `replay_manifest_json`
- optional `output_subdir`
- optional `lock_policy`
  - `min_pass_rate`
  - `max_case_fail_count`
  - `require_motion_defaults_enabled`

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_measured_replay_execution.py \
  --plan-json /path/to/measured_replay_plan.json \
  --output-root /path/to/measured_replay_outputs \
  --output-summary-json /path/to/measured_replay_summary.json
```

Exit codes:

- `0`: all packs locked (or `--allow-unlocked`)
- `2`: one or more packs contain unlocked scenarios

## Outputs

Per-pack output directory:

- `replay_report.json`
- `profile_lock_report.json`
- `locked_profiles/*.locked.json`

Aggregate summary JSON:

- `summary.pack_count`
- `summary.case_count`
- `summary.locked_count`
- `summary.unlocked_count`
- `overall_lock_pass`
- `packs[]` (artifact paths per pack)

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_measured_replay_execution.py
```
