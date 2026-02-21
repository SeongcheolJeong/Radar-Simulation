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
- [ ] M11.1: Case-level family lock manifest materialization and replay verification
- [ ] M11.2: Native scene path generator interface (`scene state -> paths_by_chirp`) and first non-frame backend stub
- [ ] M11.3: Propagation output schema expansion (`path_id`, `material_tag`, reflection order)
- [ ] M11.4: Multi-backend parity harness (`hybrid_frames` vs next backend) on shared synthetic scenes

## Exit Criteria for M11 Track

1. At least two scene backends emit identical contract shape (`paths_by_chirp`, canonical ADC).
2. `run_object_scene_to_radar_map.py` works with backend switch only from scene JSON.
3. Propagation output contains enough metadata for path-level debugging and lock triage.
