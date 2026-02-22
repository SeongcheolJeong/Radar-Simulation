# Scene Runtime Mitsuba Pilot Contract (M14.2)

## Goal

Execute the first real object-scene runtime run on a ready backend by coupling
`sionna_rt` backend to a Mitsuba-based runtime provider.

## Why This Path

- Current host Python is `3.9`, so full `sionna + tensorflow` runtime is not immediately usable.
- `sionna-rt` dependency stack (`mitsuba`, `drjit`) is installable in a Python `3.11` venv.
- This enables a real ray-intersection-backed runtime pilot without pre-exported path JSON.

## Scope

1. Add runtime provider:
   - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/runtime_providers/mitsuba_rt_provider.py`
2. Add pilot runner:
   - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_mitsuba_pilot.py`
3. Add validator:
   - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_mitsuba_pilot.py`

Provider behavior:

- Build simple Mitsuba scene from runtime-input spheres
- Ray-cast from ego origin to target directions
- Convert intersection to canonical path payload (`delay`, `doppler`, `unit_direction`, `amp_complex`)
- Return `paths_by_chirp`

## Validation

Run in runtime venv:

```bash
PYTHONPATH=src /Users/seongcheoljeong/Documents/Codex_test/.venv-sionna311/bin/python \
  /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_mitsuba_pilot.py
```

## Acceptance

M14.2 is accepted only if:

1. runtime provider path executes with Mitsuba ray intersection (no pre-exported path JSON)
2. scene pipeline outputs canonical artifacts (`path_list`, `adc_cube`, `radar_map`)
3. output metadata records `runtime_resolution.mode = runtime_provider`
