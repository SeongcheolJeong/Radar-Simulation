# Output Contracts

## 1) Path List Contract

Primary unit: chirp-local path record.

Required fields per path:

- `delay_s: float`
- `doppler_hz: float`
- `unit_direction: [ux, uy, uz]` (normalized)
- `amp_complex: {re, im}` (serialized form; in-memory field is `amp: complex`)
- `path_id: str` (non-empty)
- `material_tag: str` (non-empty)
- `reflection_order: int` (`>= 0`)

Recommended optional fields:

- `aod_az_deg`, `aod_el_deg`
- `aoa_az_deg`, `aoa_el_deg`
- `pol_matrix` (`2x2` complex, flattened in row-major `[m00,m01,m10,m11]`)

Container:

- `paths_by_chirp[k] -> list[Path]`

## 2) Raw ADC Cube Contract

Canonical shape:

- `adc[sample, chirp, tx, rx]`

Type:

- complex64 (or equivalent pair of float32 real/imag fields)

Interpretation:

- In TDM, only one `tx` index is active per chirp.
- Inactive TX slices must remain near zero.

## 3) Metadata Contract

Minimum metadata keys:

- `fc_hz`
- `slope_hz_per_s`
- `fs_hz`
- `samples_per_chirp`
- `tx_schedule`
- `tx_pos_m`
- `rx_pos_m`
- `timestamp_ref_s`

Scene-pipeline `radar_map.npz` metadata extensions:

- `path_contract_summary` (validator counts for serialized `PathList`)
- `compensation_summary` (optional; present when `backend.radar_compensation` is configured)

## 4) Derived Views

Optional derived view:

- `virtual[sample, chirp, channel]` where `channel = tx * n_rx + rx`

Derived views must not replace canonical 4D storage.
