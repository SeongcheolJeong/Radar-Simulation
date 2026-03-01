# PO-SBR Linux Runtime Runbook

## Objective

Execute `M14.6` fully on this Linux+NVIDIA PC with local scripts only (no macOS <-> Linux remote orchestration required).

## Repository Root

```bash
export REPO_ROOT=/home/seongcheoljeong/workspace/Radar-Simulation
cd "$REPO_ROOT"
```

## Required Host Baseline

1. OS: Linux
2. GPU runtime: `nvidia-smi` available
3. Python modules/runtime (bootstrap will provision):
   - `rtxpy` (modified PO-SBR-required build)
   - `igl` (libigl python bindings)
4. Local references:
   - `external/rtxpy-mod` (bootstrap clones it automatically when missing)
   - `external/PO-SBR-Python` (local one-shot clones it automatically when missing)

## Local One-Shot Run (Recommended)

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
bash scripts/run_m14_6_local_linux_full.sh
```

Useful options:

1. `--skip-bootstrap` (when `.venv-po-sbr` already prepared)
2. `--no-apply-finalize` (if you want check-only mode)
3. `--python-bin /abs/path/to/python`
4. `--output-root /abs/path`
5. `--summary-json /abs/path/to/scene_runtime_po_sbr_pilot_m14_6_linux.json`
6. `--closure-json /abs/path/to/m14_6_closure_readiness_linux.json`
7. `--po-sbr-repo-url https://...` (override clone URL when `external/PO-SBR-Python` is missing)

## Manual Step-by-Step (Local)

### 1) Bootstrap Linux runtime

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
bash scripts/bootstrap_po_sbr_linux_env.sh .venv-po-sbr external/rtxpy-mod
```

### 2) Preflight pilot (`--allow-blocked`)

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_scene_runtime_po_sbr_pilot.py \
  --output-root data/runtime_pilot/po_sbr_runtime_pilot_v1 \
  --output-summary-json docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json \
  --allow-blocked
```

Expected on ready host:

- `pilot_status = executed`

### 3) Strict execution

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
PYTHON_BIN=.venv-po-sbr/bin/python bash scripts/run_m14_6_po_sbr_linux_strict.sh \
  data/runtime_pilot/po_sbr_runtime_pilot_v1 \
  docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json \
  external/PO-SBR-Python \
  geometries/plate.obj
```

Strict wrapper path handling:

1. script normalizes `output-root`, `summary-json`, and `po-sbr-repo-root` to absolute paths before validation
2. explicit absolute paths are still recommended for reproducible logs

### 4) Closure readiness

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_m14_6_closure_readiness.py \
  --linux-summary-json docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json \
  --output-summary-json docs/reports/m14_6_closure_readiness_linux.json
```

### 5) Optional finalize helper

```bash
cd /home/seongcheoljeong/workspace/Radar-Simulation
PYTHONPATH=src .venv-po-sbr/bin/python scripts/finalize_m14_6_from_linux_report.py \
  --linux-summary-json docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json \
  --closure-summary-json docs/reports/m14_6_closure_readiness_linux.json \
  --apply
```

## Success Criteria

1. strict summary JSON includes:
   - `pilot_status = executed`
   - `path_count > 0`
   - `runtime_resolution.mode = runtime_provider`
2. strict summary passes validator:
   - `PYTHONPATH=src .venv-po-sbr/bin/python scripts/validate_scene_runtime_po_sbr_executed_report.py --summary-json docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json`
3. closure summary includes `ready = true`
4. artifact files exist under output root:
   - `path_list.json`
   - `adc_cube.npz`
   - `radar_map.npz`
