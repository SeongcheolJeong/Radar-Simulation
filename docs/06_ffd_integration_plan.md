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

3. Validation scripts (Implemented)
- parser/interpolation validation:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_ffd_parser.py`
- isotropic vs constant-pattern gain scaling integration:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_ffd_pipeline_integration.py`
- CLI wiring validation:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_ingest_cli_with_ffd.py`

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

- Add tests against a real HFSS-exported `.ffd` file artifact.
- Extend polarization handling from fixed weights to full Jones-matrix flow.
