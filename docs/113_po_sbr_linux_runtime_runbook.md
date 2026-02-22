# PO-SBR Linux Runtime Runbook

## Objective

Execute `M14.6` real runtime pilot on a Linux host with NVIDIA GPU runtime.

## Required Host Baseline

1. OS: Linux
2. GPU runtime: `nvidia-smi` available
3. Python modules:
   - `rtxpy` (modified PO-SBR-required build)
   - `igl` (libigl python bindings)
4. reference repo available:
   - `/Users/seongcheoljeong/Documents/Codex_test/external/PO-SBR-Python`

## Preflight Check (same pilot runner)

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_po_sbr_pilot.py \
  --output-root /Users/seongcheoljeong/Documents/Codex_test/data/runtime_pilot/po_sbr_runtime_pilot_v1 \
  --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json \
  --allow-blocked
```

Expected on ready Linux host:

- `pilot_status` becomes `executed` (not `blocked`)

## Environment Bootstrap (Linux)

If `rtxpy`/`igl` are missing, run:

```bash
bash /Users/seongcheoljeong/Documents/Codex_test/scripts/bootstrap_po_sbr_linux_env.sh \
  /Users/seongcheoljeong/Documents/Codex_test/.venv-po-sbr \
  /Users/seongcheoljeong/Documents/Codex_test/external/rtxpy-mod
```

This script:

1. creates/updates a Python venv
2. installs baseline modules (`numpy`, `matplotlib`, `libigl`)
3. clones/updates modified `rtxpy` and installs it editable
4. optionally installs `cupy` when CUDA toolkit is detectable

## Real Pilot Run (strict)

```bash
bash /Users/seongcheoljeong/Documents/Codex_test/scripts/run_m14_6_po_sbr_linux_strict.sh \
  /Users/seongcheoljeong/Documents/Codex_test/data/runtime_pilot/po_sbr_runtime_pilot_v1 \
  /Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json \
  /Users/seongcheoljeong/Documents/Codex_test/external/PO-SBR-Python \
  geometries/plate.obj
```

## Success Criteria

1. summary JSON:
   - `pilot_status = executed`
   - `path_count > 0`
   - `runtime_resolution.mode = runtime_provider`
   - passes validator:
     - `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_runtime_po_sbr_executed_report.py --summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json`
2. artifacts generated:
   - `path_list.json`
   - `adc_cube.npz`
   - `radar_map.npz`
3. closure gate:
   - `PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_m14_6_closure_readiness.py --linux-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_po_sbr_pilot_m14_6_linux.json --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/m14_6_closure_readiness_linux.json`
   - output must include `ready=true`
