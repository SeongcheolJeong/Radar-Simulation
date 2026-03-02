# AVx-lite Open Source Architecture Spec (One Page)

## Purpose

Define a practical AVx-lite architecture using open-source components:
`(Scene/Traffic) + (Multipath RT) + (Radar Baseband/ADC) + (Processing/V&V)`.

Goal: fast iteration with realistic multipath/ghost behavior and measurable parity gates.

## Module Stack

1. Scene/Traffic
   - `CARLA` for dynamic world, actors, and traffic.
   - `scenariogeneration` / `py-osc2` for OpenSCENARIO/OpenDRIVE generation and replay.
2. Multipath RT
   - `Sionna RT` (Mitsuba-backed) to generate geometric/radio path candidates.
3. Radar Baseband/ADC
   - AVx-lite canonical `PathList -> I/Q` synthesizer.
   - `RadarSimPy` used as processing utility layer (not strict world truth source).
4. Processing/V&V
   - Range-Doppler / Range-Angle maps, parity/KPI metrics, readiness gates.
5. EM/Antenna Pattern Asset Pipeline (HFSS alternative)
   - `openEMS` (or `gprMax`) to produce far-field pattern assets.
   - Store complex manifold assets for Tx/Rx usage in radar synthesis.

## Canonical Interfaces

### 1) PathList Contract (engine boundary)

Per-path required fields:
- `delay_s`
- `doppler_hz`
- `unit_direction = [ux, uy, uz]`
- `amp_complex = {re, im}` (or equivalent complex scalar)
- `material_tag`
- `reflection_order`

Per-frame output:
- `paths_by_chirp: List[List[path]]`

This keeps Scene/RT and Baseband loosely coupled and swappable.

### 2) Antenna Pattern Asset Contract (EM boundary)

Store as HDF5/NPZ:
- axes: `freq_hz`, `theta_deg`, `phi_deg`
- fields: `Etheta_complex`, `Ephi_complex` for Tx/Rx

Rule: keep complex phase; avoid magnitude-only manifold for angle fidelity.

## Radar-Specific Compensation Layer (must-have on top of RT)

1. Monostatic RCS/scattering normalization by target/material class.
2. Specular + diffuse/clutter composition.
3. Wideband FMCW handling across chirp bandwidth (frequency interpolation).
4. MIMO manifold phase-consistent injection.

Without this layer, multipath topology may look correct while radar outputs are not AVx-like.

## Delivery Phases

### MVP (fastest useful)

`CARLA + Sionna RT(PathList) + AVx-lite I/Q synthesis + RadarSimPy processing`.

Acceptance:
- dynamic scenarios run end-to-end
- stable `path_list.json`, `adc_cube.npz`, `radar_map.npz`
- parity gate passes for strict equivalence profiles

### V1 (AVx-like realism)

Add:
- complex antenna manifold assets
- 2-bounce multipath handling
- clutter/background model
- RCS/material lookup refinement

Acceptance:
- ghost behavior appears in expected profiles
- informational realism profiles improve without breaking strict gate profiles

## KPI and Gate Policy

1. `equivalence_strict` profiles: hard gate (`campaign_status=ready` required).
2. `realism_informational` profiles: tracked and trended, not blocking.
3. Primary metrics:
   - RD/RA shape NMSE
   - peak bin errors (range/doppler/angle)
   - centroid/spread errors
4. Report artifacts:
   - golden-path summary
   - KPI campaign summary
   - scenario matrix summary

## Risks and Mitigations

1. License risk (`GPL/AGPL` components):
   - isolate solver/runtime service boundary and review redistribution model.
2. Coordinate-frame drift:
   - enforce one canonical frame transform module and regression tests.
3. Reproducibility drift across environments:
   - lock references, pin dependencies, and keep deterministic validators.

## Immediate Repo Execution Plan

1. Keep `PathList` as fixed internal contract across backends.
2. Integrate CARLA exporter into existing scene pipeline input path.
3. Add radar compensation layer as a separate module (RCS/clutter/wideband/manifold).
4. Add antenna asset loader for complex manifold tables.
5. Extend parity matrix with multipath/ghost-focused profiles.
6. Keep strict/informational profile split in readiness gates.
7. Track licensing notes for EM solver selection before packaging.

Status update (2026-03-02):

- Steps 1, 2, 3, 4, 5, 6, and 7 are now completed in-repo (`path_contract`, CARLA bridge, compensation layer, antenna complex-manifold asset loader, profile expansion, strict/informational gate split, EM solver packaging/license boundary notes).
- Compensation tuning + profile lock freeze pipeline is now implemented (`tune_radar_compensation_presets.py` + lock-aware golden/matrix runners).
- Packaging/license boundary contract is tracked via:
  - `docs/em_solver_packaging_policy.json`
  - `docs/272_em_solver_packaging_license_boundary_contract.md`
  - `scripts/validate_em_solver_packaging_policy.py`
