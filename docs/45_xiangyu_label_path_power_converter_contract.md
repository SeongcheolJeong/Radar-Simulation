# Xiangyu Label -> Path-Power Samples Contract

## Goal

Build `path_power_samples.csv` directly from Xiangyu public dataset assets:

- `radar_raw_frame/*.mat` (or converted `.npz`)
- `text_labels/*.csv`

without requiring RT `path_list.json`.

## Input

- ADC frames (`.mat` or `.npz`)
- Xiangyu label CSV rows (`uid,class,px,py,wid,len`)

## Core Mapping

Per label row:

- `range_m = sqrt(px^2 + py^2)`
- `az_rad = atan2(px, py)`
- `el_rad = 0.0`
- `observed_amp = sqrt(max(ra_power_patch))`

`ra_power_patch` is sampled from RA map estimated from the corresponding ADC frame.

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_path_power_samples_from_xiangyu_labels.py \
  --adc-root /path/to/Automotive/2019_04_09_bms1000/radar_raw_frame \
  --labels-root /path/to/Automotive/2019_04_09_bms1000/text_labels \
  --output-csv /path/to/path_power_samples.csv \
  --output-meta-json /path/to/path_power_samples.meta.json \
  --scenario-id xiangyu_bms1000 \
  --adc-type mat \
  --adc-order scrt
```

## Output CSV

Columns include:

- `scenario_id, chirp_idx, path_idx, frame_idx`
- `range_m, az_rad, el_rad, observed_amp`
- label trace fields: `uid, class_id, px_m, py_m, wid_m, len_m`
- sampled indices: `range_bin, angle_bin`

The output is directly consumable by:

- `/Users/seongcheoljeong/Documents/Codex_test/scripts/fit_path_power_model_from_csv.py`
- `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_path_power_fit_batch.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_path_power_samples_from_xiangyu_labels.py
```
