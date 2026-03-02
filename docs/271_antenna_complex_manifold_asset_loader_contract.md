# Antenna Complex-Manifold Asset Loader Contract (M18.37)

## Goal

Add open-source antenna manifold asset ingestion (`openEMS`/`gprMax` export -> canonical asset) and bind it to the radar compensation manifold path.

## Module

- implementation:
  - `src/avxsim/antenna_manifold_asset.py`
- compensation integration:
  - `src/avxsim/radar_compensation.py`
- scene-json relative path resolution:
  - `src/avxsim/scene_pipeline.py`

## Asset Contract

Supported file formats:

1. `.npz`
2. `.h5` / `.hdf5` (requires `h5py`)

Required axes:

- `freq_hz`
- `theta_deg`
- `phi_deg`

Required Tx/Rx complex fields:

- `tx_etheta`, `tx_ephi`, `rx_etheta`, `rx_ephi`

Accepted aliases include common variants such as:

- `etheta_tx`, `ephi_tx`, `etheta_rx`, `ephi_rx`
- `Etheta_tx_re` / `Etheta_tx_im` style real/imag pairs

Field grid shape is normalized to:

- `(n_freq, n_theta, n_phi)`

Interpolation behavior:

- trilinear (`freq` + `theta` + periodic `phi`)
- `phi` wraps by `360 deg`

## Scene Backend Config Extension

`backend.radar_compensation.manifold` now supports:

- `asset_path: str` (optional)
- `asset_frequency_hz: float` (optional, default: `radar.fc_hz`)
- `asset_gain_scale: float` (optional, default: `1.0`)
- `asset_tx_pol_weights: [w_theta, w_phi]` (optional, default `[1,0]`)
- `asset_rx_pol_weights: [w_theta, w_phi]` (optional, default `[1,0]`)

Notes:

- if `asset_path` is relative in scene JSON mode, it is resolved relative to the scene JSON directory
- manifold polynomial terms (`mag_db_*`, `phase_deg_*`) remain active and multiply with sampled asset gain

## Metadata Contract

`radar_map.npz` `metadata_json.compensation_summary` now includes:

- `manifold_asset_enabled`
- `manifold_asset_path`
- `manifold_asset_frequency_hz`
- `manifold_asset_gain_scale`

## Validation

```bash
PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_antenna_complex_manifold_asset_loader.py
```
