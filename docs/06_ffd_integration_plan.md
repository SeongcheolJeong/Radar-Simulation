# Next Step: FFD Integration Plan

## Objective

Replace isotropic antenna gain with HFSS exported element patterns (`.ffd`).

## Deliverables

1. `src/avxsim/ffd.py`
- parse `.ffd` text
- load angular grid
- expose complex field lookup

2. `FfdAntennaModel` implementation
- `tx_gain(tx_idx, path) -> complex`
- `rx_gain(path, n_rx) -> complex[n_rx]`

3. Validation script
- compare isotropic vs flat-pattern `.ffd` output
- verify gain scaling and phase continuity across azimuth sweep

## Data Contract Extension

Each pattern query receives:

- angle (az, el)
- polarization basis (`etheta`, `ephi`)
- element index (tx or rx)

## Acceptance Criteria

- parser handles at least one real exported `.ffd` sample
- interpolation error baseline documented
- step-1 validation still passes with isotropic fallback path

