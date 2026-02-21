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

## Optional `.ffd` Inputs

CLI options:

- `--tx-ffd-glob "/path/to/tx*.ffd"`
- `--rx-ffd-glob "/path/to/rx*.ffd"`
- `--ffd-field-format {auto|real_imag|mag_phase_deg}`
- `--use-jones-polarization`
- `--global-jones-json /path/to/global_jones.json`
- `--scenario-profile-json /path/to/scenario_profile.json`

When set, the synthesizer uses `FfdAntennaModel` instead of isotropic gains.

## Optional Estimation/Motion Compensation Inputs

CLI options:

- `--run-hybrid-estimation`
- `--estimation-nfft`
- `--estimation-range-bin-length`
- `--estimation-doppler-window`
- `--enable-motion-compensation`
- `--disable-motion-compensation`
- `--motion-comp-fd-hz`
- `--motion-comp-chirp-interval-s`
- `--motion-comp-reference-tx`

When motion compensation is enabled, angle estimation uses TDM slot phase compensation.
If `--scenario-profile-json` is provided, global Jones and motion defaults are loaded from profile (CLI explicit options override profile values).

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

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_motion_comp.py
```

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_profile_defaults.py
```
