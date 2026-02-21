# Xiangyu Raw ADC Quickstart

## Goal

Convert one sequence from the public Raw ADC automotive dataset into this repository's measured-pack flow.

Dataset reference repo:

- `/Users/seongcheoljeong/Documents/Codex_test/external/Raw_ADC_radar_dataset_for_automotive_object_detection`

## Step 0: Download Data

The reference repo provides links for full dataset download (Google Drive / IEEE Dataport). After download/unzip, assume layout:

```text
/your_data/Automotive/
  2019_04_09_bms1000/
    radar_raw_frame/*.mat
    images_0/*
    text_labels/*
```

## Step 1: Extract MAT -> ADC NPZ

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/extract_mat_adc_to_npz.py \
  --input-root /your_data/Automotive/2019_04_09_bms1000/radar_raw_frame \
  --output-root /tmp/adc_npz_bms1000 \
  --mat-glob "*.mat" \
  --max-files 128
```

## Step 2: Build Pack From ADC NPZ

Xiangyu dataset documented radar tensor order is `samples, chirps, receivers, transmitters`, so use `--adc-order scrt`.

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_pack_from_adc_npz_dir.py \
  --input-root /tmp/adc_npz_bms1000 \
  --input-glob "*.npz" \
  --output-pack-root /tmp/packs/pack_bms1000 \
  --scenario-id bms1000_v1 \
  --adc-order scrt \
  --nfft-doppler 256 \
  --nfft-angle 64 \
  --range-bin-limit 128
```

## Step 3: Build Plan and Execute

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_measured_replay_plan.py \
  --packs-root /tmp/packs \
  --output-plan-json /tmp/packs/measured_replay_plan.json
```

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_measured_replay_execution.py \
  --plan-json /tmp/packs/measured_replay_plan.json \
  --output-root /tmp/measured_replay_outputs \
  --output-summary-json /tmp/measured_replay_summary.json \
  --allow-unlocked
```

## Notes

- This is a baseline FFT conversion path for onboarding and parity workflow bring-up.
- After first run, lock variable selection and ADC order in scenario notes for reproducibility.
