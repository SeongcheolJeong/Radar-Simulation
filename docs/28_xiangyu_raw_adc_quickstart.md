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

Install required Python packages first:

```bash
python3 -m pip install --user scipy h5py gdown
```

If you only want a fast first validation run, extract one sequence only (instead of full unzip):

```bash
mkdir -p /tmp/xiangyu_subset && \
unzip -q -n /your_data/xiangyu_raw_adc.zip \
  "Automotive/2019_04_09_bms1000/radar_raw_frame/*" \
  -d /tmp/xiangyu_subset
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

## Optional: One-command Pipeline

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_dataset_onboarding_pipeline.py \
  --input-type mat \
  --input-root /tmp/xiangyu_subset/Automotive/2019_04_09_bms1000/radar_raw_frame \
  --scenario-id xiangyu_2019_04_09_bms1000_v1 \
  --work-root /tmp/xiangyu_onboarding_run1 \
  --mat-glob "*.mat" \
  --max-files 128 \
  --adc-order scrt \
  --nfft-doppler 256 \
  --nfft-angle 64 \
  --range-bin-limit 128 \
  --allow-unlocked
```

## Optional: Rebuild Profile From Pack and Re-run Strict Lock

If baseline replay is unlocked, rebuild profile thresholds from pack candidates, then run replay without `--allow-unlocked`:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_scenario_profile_from_pack.py \
  --pack-root /tmp/xiangyu_onboarding_run1/packs/pack_xiangyu_2019_04_09_bms1000_v1 \
  --threshold-quantile 1.0 \
  --threshold-margin 1.05 \
  --threshold-floor none \
  --backup-original
```

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_measured_replay_execution.py \
  --plan-json /tmp/xiangyu_onboarding_run1/measured_replay_plan.json \
  --output-root /tmp/xiangyu_onboarding_run1/measured_replay_outputs_tuned_strict \
  --output-summary-json /tmp/xiangyu_onboarding_run1/measured_replay_summary_tuned_strict.json
```

## Notes

- This is a baseline FFT conversion path for onboarding and parity workflow bring-up.
- After first run, lock variable selection and ADC order in scenario notes for reproducibility.
