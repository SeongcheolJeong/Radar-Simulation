# AVX-Like Frontend Dashboard Usage

## Purpose

Use this document when you want the simpler dashboard path instead of Graph Lab.

This path is best for:

- a lightweight demo
- a quick API/dashboard smoke run
- a presentation-friendly view of generated outputs

For the richer operator workflow, use [Graph Lab UX Manual](300_graph_lab_ux_manual.md).

For a button-by-button manual of the classic dashboard, use [Classic Dashboard UX Manual](308_classic_dashboard_ux_manual.md).

## Run

Recommended:

```bash
PY_BIN=.venv/bin/python scripts/run_web_e2e_dashboard_local.sh 8080 8099
```

Open:

- `http://127.0.0.1:8080/frontend/avx_like_dashboard.html?summary=/docs/reports/frontend_quickstart_v1.json&api=http://127.0.0.1:8099`

Quick health check:

```bash
curl http://127.0.0.1:8099/health
```

## What The Launcher Does

The launcher:

1. builds demo artifacts under `data/demo/frontend_quickstart_v1`
2. writes `docs/reports/frontend_quickstart_v1.json`
3. starts the API on `:8099`
4. starts the static dashboard server on `:8080`

## Main Screen

![Classic dashboard full view](reports/classic_dashboard_snapshots/latest/dashboard_full.png)

Annotated:

![Classic dashboard annotated](reports/classic_dashboard_snapshots/latest/dashboard_full_annotated.png)

## What The Dashboard Reads

From the summary JSON:

- radar metadata
- first-chirp path summary
- RD/RA top-peak metadata
- output contract paths

From the generated artifact folder:

- `rd_map.png`
- `ra_map.png`
- `adc_tx0_rx0.png`
- `path_scatter_chirp0.png`

## Core Buttons

| Button | Meaning |
| --- | --- |
| `Refresh Outputs` | reload summary JSON and refresh the view |
| `Run Scene on API` | submit the scene to the API backend |
| `Pin Baseline` | record the current run as baseline |
| `Compare` | compare reference and candidate runs |
| `Policy Verdict` | compute decision policy outcome |
| `Run Regression Session` | execute a multi-candidate regression session |
| `Refresh History` | reload session/export history |
| `Export Session` | export the selected regression session |
| `Review Bundle + Copy Path` | package review evidence and copy the path |
| `Export Decision Report (.md)` | export a stakeholder-facing report |

## Known Limits

- browser-side UI is not the simulation engine
- summary and API data must exist first
- opening the page via `file://` is not supported

## Related Documents

- [Classic Dashboard UX Manual](308_classic_dashboard_ux_manual.md)
- [Classic Dashboard UX Manual (Korean)](309_classic_dashboard_ux_manual_ko.md)
- [Graph Lab UX Manual](300_graph_lab_ux_manual.md)
