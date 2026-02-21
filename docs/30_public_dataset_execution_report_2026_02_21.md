# Public Dataset Execution Report (2026-02-21)

## Objective

Run the real public measured-data onboarding path with Xiangyu Raw ADC and verify the repository pipeline works end-to-end.

## Dataset and Paths

- Downloaded zip:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc.zip`
- Validation subset extracted:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_bms1000/radar_raw_frame`
- Subset size:
  - 897 MAT frames, ~897 MB

## Executed Command

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_dataset_onboarding_pipeline.py \
  --input-type mat \
  --input-root /Users/seongcheoljeong/Documents/Codex_test/data/public/xiangyu_raw_adc_extracted/Automotive/2019_04_09_bms1000/radar_raw_frame \
  --scenario-id xiangyu_2019_04_09_bms1000_v1 \
  --work-root /Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run1 \
  --mat-glob "*.mat" \
  --max-files 128 \
  --adc-order scrt \
  --nfft-doppler 256 \
  --nfft-angle 64 \
  --range-bin-limit 128 \
  --allow-unlocked
```

## Result Summary

- Pipeline status: success
- `replay_exit_code`: `0`
- Output root:
  - `/Users/seongcheoljeong/Documents/Codex_test/data/public/onboarding_runs/xiangyu_bms1000_run1`
- Pack produced:
  - `pack_xiangyu_2019_04_09_bms1000_v1`
- Candidate estimations:
  - 128 NPZ files generated in `candidates/`
- Replay outputs present:
  - `replay_report.json`
  - `profile_lock_report.json`
  - `locked_profiles/xiangyu_2019_04_09_bms1000_v1.locked.json`

## Observed Lock State

- `overall_lock_pass`: `false`
- Summary:
  - `case_count=1`
  - `locked_count=0`
  - `unlocked_count=1`

This is expected for a first-run baseline profile before threshold tuning/profile lock finalization.

## Immediate Next Actions

1. Re-run with larger frame subset (`--max-files 512` and full 897) to observe lock stability trend.
2. Freeze profile/threshold policy for Xiangyu baseline and regenerate lock report.
3. Onboard second sequence (e.g., `2019_04_09_cms1000`) to check cross-sequence reproducibility.
