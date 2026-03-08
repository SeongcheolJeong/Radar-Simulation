# Install Guide: Base Environment

## Purpose

Use this guide when you want the minimum environment needed to:

- run the backend API
- run the classic dashboard demo
- run Graph Lab with analytic or stub-friendly paths
- run non-runtime-specific validators

This is the correct starting point for most users.

## What This Guide Installs

- Python virtual environment: `.venv`
- base Python packages:
  - `numpy`
  - `matplotlib`
- optional browser E2E package:
  - `playwright`

This guide does not install:

- RadarSimPy paid/trial runtime
- Sionna / Dr.Jit / Mitsuba runtime
- PO-SBR Linux GPU runtime

Those are covered separately:

- [Install Guide: RadarSimPy Runtime](285_install_radarsimpy_runtime.md)
- [Install Guide: Sionna-Style RT Runtime](286_install_sionna_style_rt_runtime.md)
- [Install Guide: PO-SBR Runtime](287_install_po_sbr_runtime.md)

## 1. Create The Environment

```bash
cd /path/to/myproject
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy matplotlib
```

## 2. Optional Browser E2E Support

Install only if you want Playwright-based frontend validation.

```bash
python -m pip install playwright
python -m playwright install chromium
```

## 3. Verify The Base Backend

```bash
cd /path/to/myproject
PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py
```

Expected result:

- script exits successfully
- prints `validate_web_e2e_orchestrator_api: pass`

## 4. Run The Classic Dashboard Demo

```bash
cd /path/to/myproject
PY_BIN=.venv/bin/python scripts/run_web_e2e_dashboard_local.sh 8080 8099
```

Open:

- `http://127.0.0.1:8080/frontend/avx_like_dashboard.html?summary=/docs/reports/frontend_quickstart_v1.json&api=http://127.0.0.1:8099`

What this launches:

1. demo artifact generation
2. backend API
3. static web server

## 5. Run Graph Lab

```bash
cd /path/to/myproject
PY_BIN=.venv/bin/python scripts/run_graph_lab_local.sh 8081 8101
```

Open:

- `http://127.0.0.1:8081/frontend/graph_lab_reactflow.html?api=http://127.0.0.1:8101`

## 6. Notes

- Graph Lab is static HTML + JS. A Node build is not required for local use.
- For direct Python commands, keep using `PYTHONPATH=src`.
- If you later need optional runtime tracks, keep this `.venv` for the base path and add dedicated runtime environments only when needed.
