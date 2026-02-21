# Measured Replay Plan Builder Contract

## Goal

Auto-discover measured scenario pack folders and generate `measured_replay_plan.json`.

## Folder Convention

Each pack folder contains:

- `replay_manifest.json` (required)
- `lock_policy.json` (optional)

Example:

```text
/packs_root/
  pack_chamber_v1/
    replay_manifest.json
    lock_policy.json
  pack_corridor_v2/
    replay_manifest.json
```

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_measured_replay_plan.py \
  --packs-root /path/to/packs_root \
  --output-plan-json /path/to/measured_replay_plan.json
```

Options:

- `--manifest-name` (default: `replay_manifest.json`)
- `--lock-policy-name` (default: `lock_policy.json`)
- `--recursive` (search nested folders)
- `--allow-empty` (write empty plan without failing)

## Output JSON

- `version`
- `packs[]`
  - `pack_id`
  - `replay_manifest_json`
  - `output_subdir`
  - optional `lock_policy`
- optional `metadata`

This output is consumed by:

- `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_measured_replay_execution.py`

If packs do not already have `replay_manifest.json`, generate them first:

- `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_replay_manifest_from_pack.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_measured_replay_plan_builder.py
```
