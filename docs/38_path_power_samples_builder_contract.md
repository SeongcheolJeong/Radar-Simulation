# Path Power Samples Builder Contract

## Goal

Generate path-power fitting CSV from `path_list.json` produced by ingest pipeline.

## Input

- `path_list.json` from:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_hybrid_ingest_to_adc.py`

Each path row requires:

- `delay_s`
- `unit_direction` (`ux, uy, uz`)
- `amp_complex`

## Output CSV Columns

- `scenario_id`
- `chirp_idx`
- `path_idx`
- `range_m` (`delay_s * c / 2`)
- `az_rad`
- `el_rad`
- `observed_amp` (`abs(amp_complex)`)

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_path_power_samples_from_path_list.py \
  --input-path-list-json /path/to/path_list.json \
  --output-csv /path/to/path_power_samples.csv \
  --scenario-id demo_scenario \
  --max-paths-per-chirp 16 \
  --sort-by-amp-desc
```

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_samples_builder.py
```
