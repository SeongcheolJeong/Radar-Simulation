# Next Step: FFD Integration Plan

## Objective

Replace isotropic antenna gain with HFSS exported element patterns (`.ffd`).

## Deliverables (Status)

1. `src/avxsim/ffd.py` (Implemented)
- parse `.ffd` text
- load angular grid
- complex field lookup with periodic-phi interpolation

2. `FfdAntennaModel` implementation (Implemented)
- `tx_gain(tx_idx, path) -> complex`
- `rx_gain(path, n_rx) -> complex[n_rx]`
- Jones-vector APIs:
  - `tx_jones(tx_idx, path) -> complex[2]`
  - `rx_jones(path, n_rx) -> complex[n_rx,2]`
- Global calibration matrix hook:
  - synthesis option `global_jones_matrix` (`2x2` complex)
  - effective path matrix: `J_global * J_path`

3. Validation scripts (Implemented)
- parser/interpolation validation:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_ffd_parser.py`
- real-sample regression validation:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_ffd_real_sample_regression.py`
- isotropic vs constant-pattern gain scaling integration:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_ffd_pipeline_integration.py`
- CLI wiring validation:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_ffd.py`
- Jones flow validation:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_jones_polarization_flow.py`

## Data Contract Extension

Each pattern query receives:

- angle (az, el)
- polarization basis (`etheta`, `ephi`)
- element index (tx or rx)

## Acceptance Criteria

- parser handles a structured `.ffd` sample: pass
- interpolation and periodic-phi sanity checks: pass
- step-1 validation still passes with isotropic fallback path: pass

## Remaining Work

- Generate real calibration sample sets and tune `global_jones_matrix` per scenario.
