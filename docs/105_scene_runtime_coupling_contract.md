# Scene Runtime Coupling Feasibility Contract (M14.0)

## Goal

Prototype a direct runtime-coupling path for `sionna_rt` and `po_sbr_rt` backends so object-scene execution can run without pre-exported path JSON.

## Scope

Add optional runtime provider invocation in scene backends:

- `backend.runtime_provider`: `module:function`
- `backend.runtime_input`: object payload passed to provider
- `backend.runtime_required_modules`: optional list of required Python modules
- `backend.runtime_failure_policy`: `error` or `use_static`

Static path payload inputs remain valid as primary/fallback:

- `paths_payload`
- `sionna_paths_json` / `po_sbr_paths_json`

## Runtime Resolution Modes

Backend execution records runtime resolution in `radar_map.npz` metadata:

1. `static_only`
2. `runtime_provider`
3. `runtime_failed_fallback_static`

## Failure Policy

- `runtime_failure_policy=error`:
  - runtime invocation/import failure raises immediately
- `runtime_failure_policy=use_static`:
  - if static payload exists, fallback is allowed and annotated in metadata
  - if static payload is missing, raise error

## Code Paths

- Runtime utilities:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/runtime_coupling.py`
- Backend integration:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/scene_pipeline.py`
- Public exports:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/__init__.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_backend_runtime_coupling.py
```

## Acceptance

M14.0 is accepted only if:

1. `sionna_rt` and `po_sbr_rt` can run from runtime provider output without pre-exported path JSON
2. fallback policy is deterministic (`error` vs `use_static`)
3. runtime resolution mode is observable in output metadata for replay/debug triage
