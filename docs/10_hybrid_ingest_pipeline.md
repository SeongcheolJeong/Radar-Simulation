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
- `hybrid_estimation.npz` (optional, when estimation flag is enabled)

`adc_cube.npz` contains:

- `adc` (`complex64`, shape `sample, chirp, tx, rx`)
- `metadata_json` (serialized metadata string)

`hybrid_estimation.npz` contains:

- `fx_dop`, `fx_dop_win`
- `fx_dop_max`, `fx_dop_ave`
- `fx_dop_max_win`, `fx_dop_ave_win`
- `fx_ang`
- `cap_range_azimuth`
- `metadata_json`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_pipeline_output.py
```

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_bundle.py
```
