# Dataset Onboarding Pipeline Contract

## Goal

Run end-to-end onboarding in one command:

1. optional MAT extraction
2. ADC->pack conversion
3. plan build
4. replay-lock execution

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_dataset_onboarding_pipeline.py \
  --input-type adc_npz \
  --input-root /path/to/adc_npz \
  --scenario-id dataset_v1 \
  --work-root /path/to/work_root \
  --adc-order sctr \
  --allow-unlocked
```

For MAT source:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_dataset_onboarding_pipeline.py \
  --input-type mat \
  --input-root /path/to/mat_root \
  --scenario-id dataset_v1 \
  --work-root /path/to/work_root \
  --adc-order scrt \
  --recursive \
  --allow-unlocked
```

## Outputs

Under `--work-root`:

- `packs/pack_<scenario_id>/...`
- `measured_replay_plan.json`
- `measured_replay_outputs/...`
- `measured_replay_summary.json`
- `onboarding_summary.json`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_dataset_onboarding_pipeline.py
```
