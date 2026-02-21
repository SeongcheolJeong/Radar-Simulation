# Replay Manifest Builder Contract

## Goal

Build `replay_manifest.json` from one measured pack folder with minimal arguments.

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_replay_manifest_from_pack.py \
  --pack-root /path/to/pack_root
```

Default assumptions:

- profile JSON auto-detected from:
  - `scenario_profile.locked.json`
  - `scenario_profile.json`
  - `profile.json`
- candidates from `candidates/*.npz`
- output path: `<pack-root>/replay_manifest.json`

## Inputs

Pack folder:

- required: profile JSON (auto-detect or `--profile-json`)
- optional: `candidates/*.npz`
- optional sidecar metadata per candidate:
  - `<candidate>.json`
  - `<candidate>.meta.json`

## Options

- `--scenario-id`
- `--reference-estimation-npz`
- `--candidate-glob` (repeatable)
- `--exclude-glob` (repeatable)
- `--candidate-name-mode` (`stem|name|relative`)
- `--include-sidecar-metadata`
- `--allow-empty-candidates`
- `--output-manifest-json`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_replay_manifest_builder.py
```
