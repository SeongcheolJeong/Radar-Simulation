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
- `motion_compensation_defaults` (`enabled`, `fd_hz`, `chirp_interval_s`, `reference_tx`)

Optional:

- `reference_estimation_npz`
- `fit_metrics`
- `train_estimation_npz`
- `threshold_derivation`
- `motion_tuning_summary`
- `motion_tuning_summary.ranked[]` with candidate scores/metrics
- `profile_lock` (added by replay lock finalization)

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

Motion tuning manifest mode:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_scenario_profile.py \
  --scenario-id moving_target_v1 \
  --samples-npz /path/to/calibration_samples.npz \
  --reference-estimation-npz /path/to/reference_hybrid_estimation.npz \
  --motion-tuning-manifest-json /path/to/motion_tuning_manifest.json \
  --output-profile-json /path/to/scenario_profile.json
```

Manifest format:

- root object with `candidates` list (or list directly)
- each candidate has:
  - `name`
  - `estimation_npz`
  - `motion_compensation` (`enabled`, `fd_hz`, `chirp_interval_s`, `reference_tx`)

When manifest is provided, the best motion candidate is selected from parity-metric weighted score and written to `motion_compensation_defaults`.

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

## Lock Finalization

Use replay results to finalize lock status and write `*.locked.json` profiles:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/finalize_scenario_profile_lock.py \
  --replay-report-json /path/to/replay_report.json \
  --output-lock-json /path/to/profile_lock_report.json \
  --output-locked-profile-dir /path/to/locked_profiles
```
