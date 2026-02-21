# Scene Runtime Environment Probe Contract (M14.1)

## Goal

Lock a reproducible readiness gate before attempting real Sionna/PO-SBR runtime execution.

## Scope

Add a runtime probe that emits JSON summary with:

1. Python runtime info
2. required module availability
3. external repository presence
4. per-runtime `ready` decision

Runtimes covered:

- `sionna_runtime`
- `po_sbr_runtime`

## Ready Rule

Runtime is `ready=true` only when both hold:

1. at least one configured external repo path exists
2. all required Python modules are available

## Code Paths

- Probe runner:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_env_probe.py`
- Validation:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_env_probe.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_env_probe.py
```

## Acceptance

M14.1 is accepted only if:

1. probe emits deterministic summary JSON schema
2. `ready` value is consistent with module/repo conditions
3. validator enforces the consistency rule on both runtime tracks
