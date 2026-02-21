# Scene-Backend Replan (2026-02-21)

## Why Replan

Current stack is strong on `path -> adc -> rd/ra`, but bottleneck remains `object scene -> propagation path` fidelity and backend breadth.

To reduce repeated fit-loop work with low marginal gain, priority shifts to scene/propagation backend track.

## Progress Snapshot

- Implemented strongly:
  - FMCW/TDM synthesis core
  - Hybrid ingest adapter + compatibility bundle
  - RD/RA parity tooling
  - measured replay/onboarding automation
- Partial / remaining:
  - native scene backend(s) beyond frame ingest
  - richer propagation schema parity (material/reflection-order metadata)
  - cross-backend calibration consistency

## New Milestone Track

- [x] M11.0: Object-scene pipeline V0 (`scene_json -> path_list + adc + radar_map`)
- [x] M11.1: Case-level family lock manifest materialization and replay verification
- [x] M11.2: Native scene path generator interface (`scene state -> paths_by_chirp`) and first non-frame backend stub
- [x] M11.3: Propagation output schema expansion (`path_id`, `material_tag`, reflection order)
- [x] M11.4: Multi-backend parity harness (`hybrid_frames` vs next backend) on shared synthetic scenes

## Exit Criteria for M11 Track

1. At least two scene backends emit identical contract shape (`paths_by_chirp`, canonical ADC).
2. `run_object_scene_to_radar_map.py` works with backend switch only from scene JSON.
3. Propagation output contains enough metadata for path-level debugging and lock triage.

## M12 Start

- [x] M12.0: mesh/material-aware backend candidate (`mesh_material_stub`)
- [x] M12.1: scene-asset import bridge to backend manifest (`objects/materials` extraction path)
- [x] M12.2: scene-asset parser candidate (`glTF/OBJ sidecar -> asset manifest`)
- [x] M12.3: sidecar schema profile/version lock and strict-mode parse gate
- [x] M12.4: strict/non-strict compatibility matrix and bridge E2E regression lock
- [x] M12.5: real-scene asset onboarding pilot (`public glTF/OBJ sample`) and fixture-path lock
- [x] M12.6: public multi-object scene fixture pack and deterministic replay-bundle lock
- [x] M12.7: public OBJ sample parity onboarding and mixed-format fixture matrix lock
- [x] M13.0: mesh-geometry proxy extraction baseline (`centroid/area`) for auto scene-object population
- [x] M13.1: Sionna RT backend adapter and canonical parity lock
- [x] M13.2: PO-SBR backend adapter candidate (high-fidelity scattering)
- [x] M13.3: RadarSimPy periodic parity-lock automation (drift guard)
- [x] M14.0: direct Sionna/PO-SBR runtime coupling feasibility spike (no pre-exported path JSON)
- [ ] M14.1: external runtime binding pilot (`sionna`/`po-sbr` env contract + first real scene run)
