# Public Dataset Onboarding Plan

## Scope

Onboard one public radar dataset with high conversion cost into this repository's replay-lock flow.

## Candidate Priority

1. Raw ADC automotive dataset (Xiangyu Gao repo format)
2. RADIal (if raw tensors available and schema stable)
3. Others (VoD / K-Radar / RadarScenes) after format-specific feasibility check

## Why This Order

- Current pipeline expects candidate estimation NPZ (`fx_dop_win`, `fx_ang`)
- Raw ADC datasets can be transformed with deterministic FFT baseline
- Point-cloud-only datasets require additional inverse/feature reconstruction and are higher risk

## Conversion Stages

### Stage 1: Source Extraction

- MAT/HDF5 MAT -> ADC NPZ (`adc` 4D)
- Tool: `/Users/seongcheoljeong/Documents/Codex_test/scripts/extract_mat_adc_to_npz.py`

### Stage 2: Estimation Derivation

- ADC NPZ -> candidate maps (`fx_dop_win`, `fx_ang`)
- Tool: `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_pack_from_adc_npz_dir.py`

### Stage 3: Pack and Plan Assembly

- pack replay manifest build:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_replay_manifest_from_pack.py`
- multi-pack plan build:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_measured_replay_plan.py`

### Stage 4: Replay + Lock Execution

- `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_measured_replay_execution.py`

### Stage 5: One-command Orchestration

- `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_dataset_onboarding_pipeline.py`

## Acceptance Criteria

1. One public dataset sample directory converts to at least one valid measured pack
2. `run_measured_replay_execution.py` completes with artifacts generated
3. Output lock reports are reproducible for fixed input subset

## Current Status

- Stage 1: scaffold implemented
- Stage 2: baseline FFT converter implemented
- Stage 3: implemented
- Stage 4: implemented
- Real public dataset run: pending input download and schema pin
