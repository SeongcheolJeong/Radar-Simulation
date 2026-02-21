# Motion Compensation Contract

## Goal

Provide a baseline TDM virtual-array motion compensation path for angle estimation.

## Core Model

For Tx slot offset `dt_tx` and Doppler `fd`, apply per-Tx phase correction:

- `x_comp = x * exp(-j 2*pi*fd*dt_tx)`

This correction is applied on Hybrid-compatible channel matrix `H` before angle estimation.

## Core APIs

- `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/motion_compensation.py`
  - `estimate_doppler_peak_hz(...)`
  - `infer_tx_slot_offsets(...)`
  - `apply_tdm_motion_compensation_to_h(...)`

## Pipeline Integration

- `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/pipeline.py`
  - motion compensation is used only when `run_hybrid_estimation=True` and `enable_motion_compensation=True`
  - if `motion_comp_fd_hz` is omitted, Doppler is auto-estimated from RD peak
  - default `chirp_interval_s = samples_per_chirp / fs_hz`

CLI options:

- `--enable-motion-compensation`
- `--disable-motion-compensation`
- `--motion-comp-fd-hz`
- `--motion-comp-chirp-interval-s`
- `--motion-comp-reference-tx`
- `--scenario-profile-json` (loads motion defaults from profile)

Precedence:

- explicit CLI values override scenario-profile defaults
- `--disable-motion-compensation` forces off even when profile default is enabled

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_motion_compensation_core.py
```

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_motion_comp.py
```

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_profile_defaults.py
```
