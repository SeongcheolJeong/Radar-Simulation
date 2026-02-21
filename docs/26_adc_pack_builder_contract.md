# ADC Pack Builder Contract

## Goal

Convert ADC NPZ files into one measured pack directly usable by replay evaluation.

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_pack_from_adc_npz_dir.py \
  --input-root /path/to/adc_npz \
  --input-glob "*.npz" \
  --output-pack-root /path/to/pack_out \
  --scenario-id my_scenario \
  --adc-order sctr
```

## Input Contract

Each ADC NPZ should contain:

- key `adc` (default), or another 4D array via `--adc-key`
- 4D shape order specified by `--adc-order` as permutation of `s,c,t,r`

## Processing

1. reorder ADC to canonical `[sample, chirp, tx, rx]`
2. estimate RD map (`fx_dop_win`) by range/doppler FFT
3. estimate RA map (`fx_ang`) by range + virtual-array angle FFT
4. emit pack files:
   - `candidates/*.npz`
   - `scenario_profile.json`
   - `lock_policy.json`
   - `replay_manifest.json`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_adc_pack_builder.py
```
