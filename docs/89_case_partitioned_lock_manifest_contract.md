# Case-Partitioned Lock Manifest Contract

## Goal

Materialize family-partitioned fit-lock selection into case-level pack manifest, then run replay verification in one command.

This is M11.1 bridge from policy summary to executable lock artifacts.

## Core CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_case_partitioned_lock_manifest_replay.py \
  --case-partitioned-summary-json /path/to/case_partitioned_fit_lock_summary.json \
  --case caseA=/path/to/source_pack_root::/path/to/baseline_replay_report.json \
  --case caseB=/path/to/source_pack_root \
  --allow-unlocked \
  --output-root /path/to/case_partitioned_lock_run \
  --output-summary-json /path/to/case_partitioned_lock_manifest_replay_summary.json
```

## Materialization Rule

For each case label:

1. resolve `family` from `case_family_map`
2. resolve family fit from `final.selected_fit_by_family`
3. if fit exists:
   - rebuild fit-aware pack from source pack
4. else:
   - keep source pack as baseline

Result is persisted in:

- `case_level_lock_manifest.json`

## Replay Verification

Generated plan:

- `measured_replay_plan_case_partitioned.json`

Execution output:

- `measured_replay_summary_case_partitioned.json`
- per-pack replay outputs under `measured_replay_outputs/`

## Output Summary

`case_partitioned_lock_manifest_replay_summary.json` includes:

- source summary path
- materialized manifest path
- measured replay plan/summary paths
- strategy/selection mode
- per-case selected fit, resolved pack root, baseline delta (`pass_count`, `pass_rate`)

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_case_partitioned_lock_manifest_replay.py
```
