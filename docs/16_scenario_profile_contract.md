# Scenario Profile Contract

## Goal

Lock per-scenario calibration and validation settings into one JSON profile:

- global Jones matrix
- parity thresholds
- reference estimation snapshot

## Profile JSON Fields

- `version` (int)
- `scenario_id` (string)
- `created_utc` (ISO-8601 UTC string)
- `global_jones_matrix` (row-major 4 complex values as `{re,im}`)
- `parity_thresholds` (object of `*_max` values)

Optional:

- `reference_estimation_npz`
- `fit_metrics`
- `train_estimation_npz`
- `threshold_derivation`

## Build CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_scenario_profile.py \
  --scenario-id chamber_static_v1 \
  --samples-npz /path/to/calibration_samples.npz \
  --reference-estimation-npz /path/to/reference_hybrid_estimation.npz \
  --train-estimation-npz /path/to/train_1.npz \
  --train-estimation-npz /path/to/train_2.npz \
  --output-profile-json /path/to/scenario_profile.json
```

If `--reference-estimation-npz` or `--train-estimation-npz` is missing, default parity thresholds are used.

## Evaluate CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/evaluate_scenario_profile.py \
  --profile-json /path/to/scenario_profile.json \
  --candidate-estimation-npz /path/to/candidate_hybrid_estimation.npz
```

Exit codes:

- `0`: pass
- `2`: parity fail

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scenario_profile_workflow.py
```

