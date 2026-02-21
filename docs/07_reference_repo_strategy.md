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
- radarsimpy: signal-chain cross-check reference
- Raw_ADC_radar_dataset_for_automotive_object_detection: public measured raw-ADC schema reference

## Integration Pattern

1. Pull external repos into `/Users/seongcheoljeong/Documents/Codex_test/external/`.
2. Add/maintain adapters in `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/adapters/`.
3. Keep contract tests local in `/Users/seongcheoljeong/Documents/Codex_test/scripts/`.
4. For measured public datasets, keep conversion scripts in `/Users/seongcheoljeong/Documents/Codex_test/scripts/` and avoid hard-coupling external repo internals.
