# Classic Dashboard Live Checklist

## Purpose

Use this while the classic dashboard is open.

This is the shortest practical checklist for:

- first successful dashboard refresh
- API-triggered run
- compare and policy verdict
- regression export path

For the fuller explanation, use [Classic Dashboard UX Manual](308_classic_dashboard_ux_manual.md).

## Open The Dashboard

Run:

```bash
PY_BIN=.venv/bin/python scripts/run_web_e2e_dashboard_local.sh 8080 8099
```

Open:

- `http://127.0.0.1:8080/frontend/avx_like_dashboard.html?summary=/docs/reports/frontend_quickstart_v1.json&api=http://127.0.0.1:8099`

Reference screen:

![Classic dashboard annotated](reports/classic_dashboard_snapshots/latest/dashboard_full_annotated.png)

## Checklist A: First Successful Refresh

### A1. Confirm Inputs

Check:

- `Summary JSON path`
- `API base URL`
- `Scene JSON path`

Expected:

- all three inputs are populated

### A2. Refresh Outputs

Click:

1. `Refresh Outputs`

Expected:

- scene viewer is populated
- radar map panel is populated
- metrics show values
- detection table has rows

### A3. Confirm Fast Health

Check:

- API health is `200`
- dashboard status lines are not red
- no obvious empty-state error blocks are present

## Checklist B: Run The Scene Through The API

Reference controls:

![Classic dashboard controls annotated](reports/classic_dashboard_snapshots/latest/dashboard_controls_annotated.png)

Click:

1. `Run Scene on API`

Expected:

- API run status changes from idle
- a backend run is submitted
- after completion, `Refresh Outputs` reflects the updated state if needed

If it fails:

1. confirm the API base URL
2. confirm the scene JSON path
3. rerun `scripts/validate_web_e2e_orchestrator_api.py`

## Checklist C: Compare Two Runs

Fill:

1. `Baseline ID`
2. `Reference run_id`
3. `Candidate run_id`

Click:

1. `Compare`
2. `Policy Verdict`

Expected:

- compare status updates
- policy result is computed

## Checklist D: Run A Regression Session

Fill:

1. `Regression Session ID`
2. `Candidate run_ids`

Click:

1. `Run Regression Session`
2. `Refresh History`

Expected:

- session history is populated
- export history can be refreshed and selected

## Checklist E: Export

Click as needed:

1. `Export Session`
2. `Review Bundle + Copy Path`
3. `Export Decision Report (.md)`

Expected:

- export path or export status is shown
- review bundle path is available when requested
- markdown decision report is written

## Fast Failure Reading Order

If the dashboard path looks wrong, read in this order:

1. API health
2. API run status
3. compare / regression status boxes
4. output panels

Do not start from the visual panels if the API path itself is failing.

## Related Documents

- [Frontend Dashboard Usage](116_frontend_dashboard_usage.md)
- [Classic Dashboard UX Manual](308_classic_dashboard_ux_manual.md)
- [Generated Reports Index](reports/README.md)
