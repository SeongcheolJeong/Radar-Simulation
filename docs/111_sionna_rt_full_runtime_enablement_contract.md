# Sionna RT Full Runtime Enablement Contract (M14.5)

## Goal

Unlock `sionna.rt` full runtime execution on the target macOS host with a
working LLVM backend.

## Scope

1. validate a concrete `libLLVM.dylib` candidate path
2. confirm `sionna.rt` import succeeds with `DRJIT_LIBLLVM_PATH`
3. confirm runtime env probe marks `sionna_rt_full_runtime` as ready when
   override is provided
4. confirm blocker report recommendation prefers `sionna_rt_full_runtime`
   when multiple Sionna tracks are ready

## Code Paths

- probe/update:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_sionna_rt_llvm_probe.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_env_probe.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_blocker_report.py`
- priority policy:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/runtime_blockers.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_env_probe.py
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_blocker_report.py
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_sionna_rt_llvm_probe.py

DRJIT_LIBLLVM_PATH=<valid_libllvm_path> PYTHONPATH=src /Users/seongcheoljeong/Documents/Codex_test/.venv-sionna311/bin/python -c "import importlib, sionna; importlib.import_module('sionna.rt')"
```

## Acceptance

M14.5 is accepted only if:

1. LLVM probe report includes `success=true` with non-null `working_libllvm_path`
2. direct `sionna.rt` import succeeds under the same `DRJIT_LIBLLVM_PATH`
3. runtime env probe report marks `sionna_rt_full_runtime.ready=true`
4. blocker report selects `sionna_rt_full_runtime` as `next_recommended_runtime`
