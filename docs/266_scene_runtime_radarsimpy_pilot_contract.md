# Scene Runtime RadarSimPy Pilot Contract (M14.7)

## Purpose

Integrate RadarSimPy into the scene runtime path as an optional external runtime backend, without re-implementing RadarSimPy internals.

## Scope

1. add `radarsimpy_rt` backend support in scene pipeline
2. add runtime provider callable:
   - `avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths`
3. add runtime readiness probe coverage:
   - runtime id: `radarsimpy_runtime`
4. add pilot runner and deterministic validators for runtime-provider and static-fallback execution paths

## Runtime Inputs

- backend.type: `radarsimpy_rt`
- backend.runtime_provider: module:function
- backend.runtime_required_modules: defaults to `["radarsimpy"]`
- backend.runtime_failure_policy: defaults to `use_static` for deterministic fallback
- backend.runtime_input:
  - optional target parameters (`target_range_m`, `target_az_deg`, `target_el_deg`, `target_radial_velocity_mps`)
  - optional multi-target list (`targets`)

## Outputs

- canonical `path_list.json`
- canonical `adc_cube.npz`
- canonical `radar_map.npz` (includes `metadata_json.runtime_resolution`)
- pilot summary JSON:
  - `pilot_status=executed` in standard flow
  - `runtime_fallback_used=true` when RadarSimPy module is unavailable and fallback path is used
  - runtime resolution details when executed

## Acceptance

- `run_scene_runtime_env_probe.py` includes `radarsimpy_runtime`
- `run_object_scene_to_radar_map_json` accepts backend `radarsimpy_rt`
- stubbed runtime-provider integration validator passes
- pilot validator passes on hosts with and without RadarSimPy module (provider or fallback mode)

## Validation Commands

```bash
PYTHONPATH=src python3 scripts/validate_scene_backend_runtime_coupling.py
PYTHONPATH=src python3 scripts/validate_scene_runtime_radarsimpy_provider_integration_stubbed.py
PYTHONPATH=src python3 scripts/validate_run_scene_runtime_env_probe.py
PYTHONPATH=src python3 scripts/validate_run_scene_runtime_radarsimpy_pilot.py
```
