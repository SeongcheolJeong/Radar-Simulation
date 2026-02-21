# Measurement CSV Converter Contract

## Goal

Convert measured chamber/corridor capture rows into `calibration_samples.npz` without requiring path-list/ADC regeneration.

## Input CSV

Required header columns:

- `tx_theta_re`, `tx_theta_im`
- `tx_phi_re`, `tx_phi_im`
- `rx_theta_re`, `rx_theta_im`
- `rx_phi_re`, `rx_phi_im`
- `observed_re`, `observed_im`

Optional path matrix columns (all-or-none):

- `path_m00_re`, `path_m00_im`
- `path_m01_re`, `path_m01_im`
- `path_m10_re`, `path_m10_im`
- `path_m11_re`, `path_m11_im`

If optional path matrix columns are absent, identity matrix is used per sample.

Optional index trace columns:

- `chirp_idx`, `tx_idx`, `rx_idx`, `path_idx`, `frame_idx`

## Column Remap

Use a JSON map when real CSV headers differ:

- key: canonical field name above
- value: actual CSV header name

Example:

```json
{
  "observed_re": "obs_re_custom",
  "observed_im": "obs_im_custom"
}
```

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_calibration_samples_from_measurement_csv.py \
  --input-csv /path/to/measurement.csv \
  --column-map-json /path/to/column_map.json \
  --output-npz /path/to/calibration_samples.npz
```

## Output NPZ

Required arrays:

- `tx_jones` `(N,2)` complex
- `rx_jones` `(N,2)` complex
- `observed_gain` `(N,)` complex
- `path_matrices` `(N,2,2)` complex

Optional arrays:

- `chirp_idx`, `tx_idx`, `rx_idx`, `path_idx`, `frame_idx` `(N,)` int

Metadata:

- `metadata_json` with source CSV path, delimiter, column map

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_measurement_csv_converter.py
```

