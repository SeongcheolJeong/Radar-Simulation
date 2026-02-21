# Moving-Target Replay Batch Contract

## Goal

Evaluate many moving-target candidates against reference snapshots in one run, using scenario profile thresholds.

## Manifest JSON

Root can be:

- object with `cases` list
- list directly

Each case:

- `scenario_id`
- optional `profile_json`
- optional `reference_estimation_npz` (required if profile has no reference)
- optional `parity_thresholds` (required when profile is not provided)
- `candidates` (non-empty list)

Candidate fields:

- `name`
- `estimation_npz`
- optional `metadata`

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_moving_target_replay_batch.py \
  --manifest-json /path/to/replay_manifest.json \
  --output-json /path/to/replay_report.json
```

Exit codes:

- `0`: all candidates pass
- `2`: one or more candidates fail (unless `--allow-failures`)

## Output Report

- `summary`
  - `case_count`, `candidate_count`, `pass_count`, `fail_count`, `pass_rate`
- `cases[]`
  - per-case counts
  - per-candidate metrics/failures
  - profile-derived `motion_compensation_defaults` when profile is used

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_moving_target_replay_batch.py
```

