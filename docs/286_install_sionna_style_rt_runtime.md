# Install Guide: Sionna-Style RT Runtime

## Purpose

Use this guide when you want to enable:

- `High Fidelity: Sionna-style RT` in Graph Lab
- Mitsuba / Dr.Jit-backed ray-tracing path generation
- optional `sionna.rt` full-runtime experiments

## What The Frontend Track Actually Needs

For the Graph Lab preset `High Fidelity: Sionna-style RT`, the relevant required modules are:

- `mitsuba`
- `drjit`

Optional full Sionna runtime work may also require:

- `sionna`
- `tensorflow`

This repository treats those as separate readiness levels.

## 1. Create A Dedicated Runtime Environment

Recommended:

```bash
cd /path/to/myproject
python3 -m venv .venv-sionna311
. .venv-sionna311/bin/activate
python -m pip install --upgrade pip
python -m pip install mitsuba drjit
```

If you also need full Sionna runtime:

```bash
.venv-sionna311/bin/pip install sionna tensorflow
```

## 2. Verify Basic Module Imports

```bash
cd /path/to/myproject
.venv-sionna311/bin/python -c "import mitsuba, drjit; print('mitsuba+drjit ok')"
```

If you installed full Sionna:

```bash
cd /path/to/myproject
.venv-sionna311/bin/python -c "import sionna; print('sionna ok')"
```

## 3. Probe Runtime Readiness

```bash
cd /path/to/myproject
PYTHONPATH=src .venv-sionna311/bin/python scripts/run_scene_runtime_env_probe.py \
  --output-summary-json docs/reports/runtime_env_probe_sionna_latest.json
```

What to check in the output JSON:

- `runtime_report.sionna_rt_mitsuba_runtime.ready = true`

If you installed `sionna` and `tensorflow`, you can also inspect:

- `runtime_report.sionna_runtime`
- `runtime_report.sionna_rt_full_runtime`

## 4. Optional: Fix `sionna.rt` LLVM Loading

On some systems, `sionna.rt` needs an explicit `DRJIT_LIBLLVM_PATH`.

Example:

```bash
export DRJIT_LIBLLVM_PATH=/absolute/path/to/libLLVM.dylib
PYTHONPATH=src .venv-sionna311/bin/python -c "import importlib; importlib.import_module('sionna.rt'); print('sionna.rt ok')"
```

To probe candidate LLVM paths:

```bash
cd /path/to/myproject
PYTHONPATH=src .venv-sionna311/bin/python scripts/run_sionna_rt_llvm_probe.py \
  --output-summary-json docs/reports/sionna_rt_llvm_probe_latest.json
```

## 5. Use It In Graph Lab

Run Graph Lab with the dedicated Python:

```bash
cd /path/to/myproject
PY_BIN=.venv-sionna311/bin/python scripts/run_graph_lab_local.sh 8081 8101
```

In the UI:

1. choose `High Fidelity: Sionna-style RT`
2. inspect runtime diagnostics
3. confirm the backend is planned/ready instead of blocked

## 6. Notes

- The Graph Lab preset focuses on Mitsuba-style RT path generation, not necessarily the full `sionna.rt` stack.
- If `drjit`/LLVM issues block import, the next thing to verify is `DRJIT_LIBLLVM_PATH`.
- For deeper contract details, see:
  - [Sionna RT Full Runtime Enablement Contract](111_sionna_rt_full_runtime_enablement_contract.md)
  - [Sionna RT Backend Contract](102_sionna_rt_backend_contract.md)
