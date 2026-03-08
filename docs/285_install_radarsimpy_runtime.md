# Install Guide: RadarSimPy Runtime

## Purpose

Use this guide when you want to enable:

- `Low Fidelity: RadarSimPy + FFD` in Graph Lab
- RadarSimPy-backed runtime checks
- paid or trial RadarSimPy release/readiness/parity gates

## What The Repository Supports

The wrapper auto-discovers RadarSimPy from code in:

- `src/avxsim/radarsimpy_api.py`

Relevant environment variables:

- `RADARSIMPY_PACKAGE_ROOT`
- `RADARSIMPY_LIBCOMPAT_DIR`
- `RADARSIMPY_LICENSE_FILE`
- `RADARSIMPY_AUTO_DISCOVER`

Default package root search order:

1. `external/radarsimpy_trial/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU`
2. `external/radarsimpy_order_pull_latest/extracted/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU`
3. `external/radarsimpy/src`

Default libcompat search:

- `external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu`

Default license auto-discovery:

- `license_RadarSimPy_*.lic` inside discovered package locations

## 1. Base Python Environment

Start from the base environment:

- [Install Guide: Base Environment](284_install_base_environment.md)

## 2. Choose One Runtime Source

### Option A: Use Repo-Bundled / Extracted Runtime

If this repository already contains a valid RadarSimPy package under one of the default search paths, you may not need additional install work.

Check for these paths:

```bash
cd /path/to/myproject
ls external/radarsimpy_trial/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU || true
ls external/radarsimpy_order_pull_latest/extracted/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU || true
ls external/radarsimpy/src || true
```

### Option B: Point To An Explicit Package Root

If your RadarSimPy package is outside the default paths, export:

```bash
export RADARSIMPY_PACKAGE_ROOT=/absolute/path/to/RadarSimPy/package/root
export RADARSIMPY_LIBCOMPAT_DIR=/absolute/path/to/libcompat/usr/lib/x86_64-linux-gnu
```

If you have a paid license file, also export:

```bash
export RADARSIMPY_LICENSE_FILE=/absolute/path/to/license_RadarSimPy_XXXX.lic
```

### Option C: Disable Auto-Discovery And Fully Pin Paths

Use this when you want deterministic environment control.

```bash
export RADARSIMPY_AUTO_DISCOVER=0
export RADARSIMPY_PACKAGE_ROOT=/absolute/path/to/RadarSimPy/package/root
export RADARSIMPY_LIBCOMPAT_DIR=/absolute/path/to/libcompat/usr/lib/x86_64-linux-gnu
export RADARSIMPY_LICENSE_FILE=/absolute/path/to/license_RadarSimPy_XXXX.lic
```

## 3. Verify Module Loading

```bash
cd /path/to/myproject
PYTHONPATH=src .venv/bin/python -c "from avxsim.radarsimpy_api import load_radarsimpy_module; print(load_radarsimpy_module().__name__)"
```

Expected result:

- prints `radarsimpy`

## 4. Verify Runtime Readiness

```bash
cd /path/to/myproject
PYTHONPATH=src .venv/bin/python scripts/run_scene_runtime_env_probe.py \
  --output-summary-json docs/reports/runtime_env_probe_radarsimpy_latest.json
```

What to check in the output JSON:

- `runtime_report.radarsimpy_runtime.ready = true`

## 5. Verify The Frontend Low-Fidelity Track

Run Graph Lab:

```bash
cd /path/to/myproject
PY_BIN=.venv/bin/python scripts/run_graph_lab_local.sh 8081 8101
```

In the UI:

1. choose `Low Fidelity: RadarSimPy + FFD`
2. inspect runtime diagnostics
3. confirm the RadarSimPy runtime is no longer blocked

## 6. Paid / Production Validation

If you have a paid `.lic` file, run:

```bash
cd /path/to/myproject
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_paid_6m_gate_ci.sh
```

Or run the major steps directly:

```bash
cd /path/to/myproject
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_production_release_gate.py --license-file /absolute/path/to/license_RadarSimPy_XXXX.lic
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_readiness_checkpoint.py --with-real-runtime --runtime-license-tier production --license-file /absolute/path/to/license_RadarSimPy_XXXX.lic
PYTHONPATH=src .venv/bin/python scripts/validate_radarsimpy_simulator_reference_parity_optional.py --require-runtime --output-json docs/reports/radarsimpy_simulator_reference_parity_paid_6m.json
```

## 7. Notes

- Graph Lab uses RadarSimPy as the low-fidelity reference path, not as the only runtime in the repository.
- If you are using Linux trial/extracted packages, `RADARSIMPY_LIBCOMPAT_DIR` is often required.
- For deeper runtime behavior and migration history, see:
  - [Scene Runtime RadarSimPy Pilot Contract](266_scene_runtime_radarsimpy_pilot_contract.md)
  - [RadarSimPy Real Functional Migration Contract](274_radarsimpy_real_functional_migration_contract.md)
