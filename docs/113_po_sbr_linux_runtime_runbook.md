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
