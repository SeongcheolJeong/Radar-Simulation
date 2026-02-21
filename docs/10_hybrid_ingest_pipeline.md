# Hybrid Ingest Pipeline

## Objective

Provide one command that converts HybridDynamicRT frame folders to:

- canonical path list JSON
- canonical ADC cube NPZ

## Entry Points

- Pipeline function:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/pipeline.py`
  - `run_hybrid_frames_pipeline(...)`
- CLI wrapper:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_hybrid_ingest_to_adc.py`

## Outputs

- `path_list.json`
- `adc_cube.npz`

`adc_cube.npz` contains:

- `adc` (`complex64`, shape `sample, chirp, tx, rx`)
- `metadata_json` (serialized metadata string)

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_pipeline_output.py
```

