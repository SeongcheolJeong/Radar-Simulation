# Reference Repo Strategy

## Decision

Use references via local adapters, not by merging third-party internals into core modules.

## Why

- Preserve stable in-house contracts (`paths_by_chirp`, canonical 4D ADC cube).
- Decouple from frequent upstream structure changes.
- Reduce license spillover risk.
- Keep verification reproducible even when a reference backend is unavailable.

## Repositories

- HybridDynamicRT: path-generation reference
- sionna: propagation/RT reference
- PO-SBR-Python: high-fidelity scattering/SBR reference
- radarsimpy: signal-chain cross-check reference
- Raw_ADC_radar_dataset_for_automotive_object_detection: public measured raw-ADC schema reference

## Integration Pattern

1. Pull external repos into `/Users/seongcheoljeong/Documents/Codex_test/external/`.
2. Add/maintain adapters in `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/adapters/`.
3. Keep contract tests local in `/Users/seongcheoljeong/Documents/Codex_test/scripts/`.
4. For measured public datasets, keep conversion scripts in `/Users/seongcheoljeong/Documents/Codex_test/scripts/` and avoid hard-coupling external repo internals.

## Planned Integration Order (M13+)

1. M13.0: mesh-geometry proxy extractor baseline from OBJ/glTF metadata.
2. M13.1: Sionna RT backend adapter (`scene -> paths_by_chirp`) with canonical output parity gate.
3. M13.2: PO-SBR backend adapter for higher-fidelity scattering/path-power behavior.
4. M13.3: RadarSimPy parity-lock automation for periodic signal-chain drift checks (optional hard gate).

## Current Readiness Assessment

- Implemented strongly:
  - HybridDynamicRT-based ingest and Python-native signal chain
  - canonical outputs (`path list`, `raw ADC`, `radar_map`)
  - `.ffd`/Jones calibration path
  - public asset onboarding (`glTF`, `OBJ`) and deterministic fixture bundles
  - exported-path adapters: `sionna_rt`, `po_sbr_rt` + parity locks
- Remaining high-impact physics/backend work:
  - direct Sionna/PO-SBR runtime coupling (without pre-exported path payload)
  - scattering-physics fidelity tuning against measured scenarios
- RadarSimPy position:
  - useful as regression oracle
  - not required for core pipeline execution
  - periodic parity-lock automation implemented (manifest + threshold gate)
  - remains optional runtime dependency for core scene pipeline
