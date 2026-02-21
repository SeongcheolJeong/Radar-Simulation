# Profile Tuning Policy Contract

## Goal

Version and reuse profile-threshold rebuild parameters per dataset/scenario family.

## Policy JSON Schema

```json
{
  "version": 1,
  "name": "xiangyu_raw_adc_profile_tuning_v1",
  "profile_rebuild": {
    "case_index": 0,
    "reference_candidate_index": 0,
    "candidate_stride": 1,
    "max_candidates": null,
    "threshold_quantile": 1.0,
    "threshold_margin": 1.05,
    "threshold_floor": "none"
  },
  "lock_policy": {
    "min_pass_rate": 1.0,
    "max_case_fail_count": 0,
    "require_motion_defaults_enabled": false
  }
}
```

## Apply CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_scenario_profile_from_pack.py \
  --pack-root /path/to/pack_root \
  --policy-json /Users/seongcheoljeong/Documents/Codex_test/configs/profile_tuning/xiangyu_raw_adc_v1.json \
  --emit-policy-json /path/to/pack_root/profile_tuning_policy.json \
  --backup-original
```

## Precedence

When `--policy-json` is provided:

1. policy values are loaded first
2. explicitly passed CLI flags override policy values

## Output Embedding

The rebuilt `scenario_profile.json` includes:

- `profile_tuning_policy`
- `threshold_derivation` (resolved values and candidate count)

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_build_scenario_profile_from_pack.py
```
