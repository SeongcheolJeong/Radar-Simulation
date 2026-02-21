# Profile Rebuild From Pack Contract

## Goal

Rebuild `scenario_profile.json` directly from one measured pack's candidate set by deriving parity thresholds from replay-estimation metrics.

This provides a deterministic path from:

- `replay_manifest.json`
- `candidates/*.npz`

to a tuned profile that can be re-checked in strict lock mode.

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_scenario_profile_from_pack.py \
  --pack-root /path/to/pack_root \
  --policy-json /Users/seongcheoljeong/Documents/Codex_test/configs/profile_tuning/xiangyu_raw_adc_v1.json \
  --threshold-quantile 1.0 \
  --threshold-margin 1.05 \
  --threshold-floor none \
  --emit-policy-json /path/to/pack_root/profile_tuning_policy.json \
  --backup-original
```

## Inputs

- `<pack-root>/replay_manifest.json`
- `<pack-root>/scenario_profile.json` (for existing `global_jones_matrix` and motion defaults)
- candidate NPZ files referenced in manifest (`fx_dop_win`, `fx_ang`)

## Output

- default output: `<pack-root>/scenario_profile.json` (overwritten)
- optional backup: `<pack-root>/scenario_profile.default.json` (`--backup-original`)

Updated profile contains:

- `parity_thresholds` (re-derived)
- `reference_estimation_npz`
- `train_estimation_npz`
- `threshold_derivation` metadata
- `profile_tuning_policy` metadata

## Notes

- Use `threshold-floor=defaults` to clamp by baseline contract thresholds.
- Use `threshold-floor=none` to rely only on measured candidate distribution.
- If `--policy-json` is set, policy values are used and explicit CLI flags override them.
- After rebuild, run strict replay execution (without `--allow-unlocked`) to verify lock pass.

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_build_scenario_profile_from_pack.py
```
