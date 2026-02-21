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

- Stage 1: implemented and validated with Xiangyu MAT input (`adcData`)
- Stage 2: implemented and validated with `--adc-order scrt` baseline FFT conversion
- Stage 3: implemented and validated (pack + replay plan generated)
- Stage 4: implemented and validated (`run_measured_replay_execution.py` exit code `0`)
- Stage 5: implemented and validated (`run_dataset_onboarding_pipeline.py`)
- Real public dataset run: first execution complete on 2026-02-21

## First Public Run Snapshot (2026-02-21)

- Dataset: Xiangyu Raw ADC (public automotive dataset)
- Source zip: `/Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc.zip` (~15 GB)
- Subset used: `Automotive/2019_04_09_bms1000/radar_raw_frame` (897 MAT frames)
- Onboarding command:
  - `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_dataset_onboarding_pipeline.py --input-type mat --input-root /Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_bms1000/radar_raw_frame --scenario-id xiangyu_2019_04_09_bms1000_v1 --work-root /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run1 --mat-glob "*.mat" --max-files 128 --adc-order scrt --nfft-doppler 256 --nfft-angle 64 --range-bin-limit 128 --allow-unlocked`
- Output root:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run1`
- Artifact summary:
  - pack generated: 1
  - candidate estimations generated: 128
  - replay execution: success (pipeline exit code `0`)
  - profile lock summary: unlocked 1 case (baseline profile not yet locked)
