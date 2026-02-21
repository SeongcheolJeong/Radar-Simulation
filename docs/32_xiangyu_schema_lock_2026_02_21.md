# Xiangyu Schema Lock (2026-02-21)

## Purpose

Pin the first public measured dataset schema used by this repository so onboarding/replay runs are reproducible.

## Locked Schema

- Dataset family: Xiangyu Raw ADC automotive
- MAT variable: `adcData` (auto-detected 4D numeric key)
- MAT shape: `[128, 255, 4, 2]`
- ADC axis interpretation: `samples, chirps, receivers, transmitters`
- Pack builder flag: `--adc-order scrt` (reordered to internal `sctr`)

## Verified Sequences

1. `2019_04_09_bms1000`
2. `2019_04_09_cms1000`

Both sequences were checked on sampled frames and produced consistent shape/dtype with the same extraction path (`scipy.io.loadmat`).

## Executed Runs

1. BMS1000 subset 128 frames:
   - baseline replay: pass but unlocked
   - tuned profile replay (strict): lock pass
2. BMS1000 subset 512 frames:
   - baseline replay: pass but unlocked
   - tuned profile replay (strict): lock pass
3. BMS1000 full 897 frames:
   - baseline replay: pass but unlocked
   - tuned profile replay (strict): lock pass
4. CMS1000 subset 128 frames:
   - baseline replay: pass but unlocked
   - tuned profile replay (strict): lock pass

## Tuning Method

- script: `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_scenario_profile_from_pack.py`
- policy used:
  - `threshold_quantile=1.0`
  - `threshold_margin=1.05`
  - `threshold_floor=none`

## Locking Interpretation

- Baseline pack profile uses default strict parity thresholds and is expected to be conservative.
- Schema lock objective is satisfied when:
  - data extraction contract is stable
  - replay artifacts are reproducible
  - tuned profile can be finalized and pass strict lock checks.
