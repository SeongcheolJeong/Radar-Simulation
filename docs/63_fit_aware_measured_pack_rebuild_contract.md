# Fit-Aware Measured Pack Rebuild Contract

## Goal

Enable measured replay to become sensitive to path-power fit changes by rebuilding pack candidates from the same source ADC files with fit-aware proxy weighting.

## Core CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_fit_aware_pack_from_existing_pack.py \
  --source-pack-root /path/to/source_pack \
  --output-pack-root /path/to/fit_aware_pack \
  --path-power-fit-json /path/to/path_power_fit_selected.json \
  --output-summary-json /path/to/fit_aware_pack_summary.json
```

## Behavior

- candidate source list is reused from source pack candidate metadata (`source_adc_npz`)
- candidate estimation maps are rebuilt with fit proxy weighting
- source profile thresholds/calibration fields are preserved, with reference path updated to new pack
- lock policy file is copied from source pack when present

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_build_fit_aware_pack_from_existing_pack.py
```

Validation checks:

- output candidate count preserved
- candidate RD map changes vs source pack
- candidate metadata contains `path_power_fit_proxy`
- source parity thresholds preserved in rebuilt profile
