# Sionna RT LLVM Probe Contract (M14.4)

## Goal

Add deterministic probing for `sionna.rt` LLVM backend readiness by testing
candidate shared-library paths against real import execution.

## Scope

Probe runner:

- discovers default `libLLVM` candidates (env var, llvmlite, Xcode SDK paths)
- defaults to macOS-compatible SDK candidates only
- can optionally include non-macOS Xcode SDK candidates via flag
- runs baseline import probe (`sionna.rt` without env override)
- runs per-candidate import probe with `DRJIT_LIBLLVM_PATH`
- records success/failure and stderr diagnostics

## Code Paths

- runner:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_sionna_rt_llvm_probe.py`
- validation:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_sionna_rt_llvm_probe.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_sionna_rt_llvm_probe.py
```

## Acceptance

M14.4 probe is accepted only if:

1. summary JSON schema is deterministic (`success`, `working_libllvm_path`, per-probe results)
2. at least one probe (baseline) always executes
3. failures retain stderr diagnostics for blocker triage
