# MAT ADC Extractor Contract

## Goal

Extract 4D ADC arrays from MAT files into NPZ for downstream pack conversion.

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/extract_mat_adc_to_npz.py \
  --input-root /path/to/mat_root \
  --output-root /path/to/adc_npz \
  --recursive
```

## Loader Policy

- Primary: `scipy.io.loadmat` (MAT v5)
- Fallback: `h5py` (MAT v7.3 / HDF5)
- Select 4D numeric variable:
  - explicit `--mat-variable`, or
  - auto-select largest 4D numeric array

## Output

- per MAT: `adc_XXXX_<stem>.npz` with key `adc`
- index: `adc_npz_index.json`

## Notes

- MAT schema is dataset-specific; selected variable should be pinned once discovered.
- ADC dimension order is not inferred semantically; downstream conversion must pass correct `--adc-order`.

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mat_adc_extractor_core.py
```
