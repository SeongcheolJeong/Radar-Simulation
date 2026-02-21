# Jones Calibration Contract

## Goal

Estimate and apply a global Jones transfer matrix (`2x2` complex) that compensates polarization mismatch between simulation and reference measurement.

## Calibration Model

For each sample `n`:

- `y_n` : observed complex gain
- `t_n` : Tx Jones vector (`2x1`)
- `r_n` : Rx Jones vector (`2x1`)
- `P_n` : path polarization matrix (`2x2`, optional)
- `J` : global Jones transfer matrix (`2x2`, unknown)

Model:

- `y_n ≈ r_n^H * J * P_n * t_n`

`J` is solved by complex least squares (optional ridge regularization).

## Sample NPZ Format

Input to calibration script:

- `tx_jones`: shape `(N,2)`, complex
- `rx_jones`: shape `(N,2)`, complex
- `observed_gain`: shape `(N,)`, complex
- `path_matrices`: shape `(N,2,2)`, complex (optional, identity if omitted)

Builder output can also include index traces:

- `chirp_indices`, `tx_indices`, `rx_indices`, `path_indices`, `beat_hz`

## Sample Builder CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_calibration_samples_from_outputs.py \
  --path-list-json /path/to/path_list.json \
  --adc-npz /path/to/adc_cube.npz \
  --tx-ffd-glob "/path/to/tx*.ffd" \
  --rx-ffd-glob "/path/to/rx*.ffd" \
  --observed-mode normalized \
  --max-paths-per-chirp 1 \
  --output-npz /path/to/calibration_samples.npz
```

Measured CSV converter CLI:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_calibration_samples_from_measurement_csv.py \
  --input-csv /path/to/measurement.csv \
  --output-npz /path/to/calibration_samples.npz
```

`observed-mode`:

- `normalized`: divide matched-filter gain by scalar path model (`amp * phase`) to isolate polarization response
- `raw`: keep matched-filter gain as-is

## Calibration CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/fit_global_jones_matrix.py \
  --samples-npz /path/to/calibration_samples.npz \
  --ridge 1e-6 \
  --output-json /path/to/global_jones.json
```

Output JSON contains:

- `global_jones_matrix` (flattened row-major 4 complex values)
- `metrics` (`nmse`, `relative_rmse`, correlation, sample count)

## Ingest Pipeline Integration

`run_hybrid_ingest_to_adc.py` supports:

- `--global-jones-json /path/to/global_jones.json`

When set, synthesis uses:

- `J_effective = J_global * J_path`

and applies:

- `gain = rx^H * J_effective * tx`

## Validation

- Calibration core:  
  `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_global_jones_calibration.py`
- Ingest CLI integration:  
  `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_global_jones.py`
- Sample builder + fitter round-trip:  
  `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_calibration_samples_builder.py`

## Next Step

Populate `calibration_samples.npz` from measured chamber/corridor captures and lock scenario-wise calibration JSON snapshots.
