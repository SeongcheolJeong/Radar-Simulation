# Install Guide: PO-SBR Runtime

## Purpose

Use this guide when you want to enable:

- `High Fidelity: PO-SBR` in Graph Lab
- PO-SBR runtime pilot and gate workflows
- Linux GPU-backed path generation with `rtxpy` and `igl`

## Important Constraints

PO-SBR runtime is currently a Linux + NVIDIA path.

You should assume the following are required:

- Linux host
- `nvidia-smi` available
- Python environment dedicated to PO-SBR
- `rtxpy`
- `igl`

## 1. Create The Dedicated PO-SBR Environment

Use the repo bootstrap helper:

```bash
cd /path/to/myproject
bash scripts/bootstrap_po_sbr_linux_env.sh .venv-po-sbr external/rtxpy-mod
```

What this does:

1. creates or updates `.venv-po-sbr`
2. installs baseline packages
3. installs `libigl`
4. clones or updates modified `rtxpy`
5. installs editable `rtxpy`
6. optionally installs `cupy` when CUDA tooling is detectable

## 2. Verify Runtime Readiness

```bash
cd /path/to/myproject
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_scene_runtime_env_probe.py \
  --output-summary-json docs/reports/runtime_env_probe_po_sbr_latest.json
```

What to check in the output JSON:

- `runtime_report.po_sbr_runtime.ready = true`

## 3. Optional: Add Mitsuba / Dr.Jit Into The Same Environment

If you want one environment that can exercise all major backends on the same host:

```bash
cd /path/to/myproject
PYTHONPATH=src .venv-po-sbr/bin/pip install drjit mitsuba
```

## 4. Verify A PO-SBR Pilot

Preflight / pilot path:

```bash
cd /path/to/myproject
PYTHONPATH=src .venv-po-sbr/bin/python scripts/run_scene_runtime_po_sbr_pilot.py \
  --output-root data/runtime_pilot/po_sbr_runtime_pilot_v1 \
  --output-summary-json docs/reports/scene_runtime_po_sbr_pilot_local_latest.json \
  --allow-blocked
```

On a ready Linux + NVIDIA host, the pilot should move from `blocked` to `executed`.

## 5. Use It In Graph Lab

Run Graph Lab with the PO-SBR environment:

```bash
cd /path/to/myproject
PY_BIN=.venv-po-sbr/bin/python scripts/run_graph_lab_local.sh 8081 8101
```

In the UI:

1. choose `High Fidelity: PO-SBR`
2. inspect runtime diagnostics
3. confirm the backend is ready instead of blocked

## 6. Notes

- This is not a macOS-first path.
- The repo already contains a deeper Linux runbook:
  - [PO-SBR Linux Runtime Runbook](113_po_sbr_linux_runtime_runbook.md)
- For backend contract details, see:
  - [PO-SBR Backend Contract](103_po_sbr_backend_contract.md)
  - [Scene Runtime PO-SBR Pilot Contract](112_scene_runtime_po_sbr_pilot_contract.md)
