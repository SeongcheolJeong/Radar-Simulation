# Measured Dataset Conversion Plan

## Goal

When public measured datasets are heterogeneous, convert them into this repository's replay-lock workflow with minimal manual work.

Target internal contract:

1. per-pack `replay_manifest.json`
2. multi-pack `measured_replay_plan.json`
3. execution outputs (`replay_report.json`, `profile_lock_report.json`, `locked_profiles/*.locked.json`)

## Strategy

### Phase A: Pack Normalization (required)

Per scenario pack directory should contain:

- `scenario_profile.json` or `scenario_profile.locked.json`
- candidate estimation files `candidates/*.npz` (`fx_dop_win`, `fx_ang`)
- optional `lock_policy.json`

Automation:

- build per-pack manifest:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_replay_manifest_from_pack.py`
- discover all packs and build plan:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_measured_replay_plan.py`

### Phase B: Batch Replay + Lock (required)

Execute all packs in one run:

- `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_measured_replay_execution.py`

### Phase C: Dataset-specific converters (incremental)

If source dataset does not provide `fx_dop_win`/`fx_ang` NPZ directly:

1. convert source raw format to canonical intermediate
2. derive estimation maps (`fx_dop_win`, `fx_ang`)
3. write candidate NPZs into `candidates/`

Implemented baseline converters:

- source MAT -> ADC NPZ:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/extract_mat_adc_to_npz.py`
- ADC NPZ -> measured pack:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_pack_from_adc_npz_dir.py`

This phase is dataset-specific and should be added adapter-by-adapter.

## Priority Rule

1. datasets already close to NPZ/ADC arrays
2. permissive license and reproducible downloads
3. stable folder/schema over time

## Current Status

- Phase A: implemented
- Phase B: implemented
- Phase C: planned per target dataset
- Phase C: baseline converter implemented, dataset-specific schema lock pending

## Temporary Path Without Real Data

Use mock pack generator to validate full workflow end-to-end before real dataset onboarding:

- `/Users/seongcheoljeong/Documents/Codex_test/scripts/generate_mock_measured_packs.py`
- `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mock_measured_packs_e2e.py`

## Public Dataset Quickstart

- Xiangyu Raw ADC example flow:
  - `/Users/seongcheoljeong/Documents/Codex_test/docs/28_xiangyu_raw_adc_quickstart.md`
