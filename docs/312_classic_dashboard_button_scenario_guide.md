# Classic Dashboard Button Scenario Guide

## Purpose

This guide explains classic dashboard buttons by operator intent.

Use it when:

- there are too many controls in the left sidebar
- you want the shortest click path for one task
- you do not want to read the whole UX manual first

For the full screen walkthrough, use [Classic Dashboard UX Manual](308_classic_dashboard_ux_manual.md).

## Screen Reference

Full screen:

![Classic dashboard full](reports/classic_dashboard_snapshots/latest/dashboard_full.png)

Annotated full screen:

![Classic dashboard annotated](reports/classic_dashboard_snapshots/latest/dashboard_full_annotated.png)

Annotated controls:

![Classic dashboard controls annotated](reports/classic_dashboard_snapshots/latest/dashboard_controls_annotated.png)

## Scenario 1: I Just Want The Dashboard To Show Data

Use this when the page loaded but the panels still look stale.

Where:

- left sidebar, top section

Buttons:

1. `Refresh Outputs`

Expected result:

- scene viewer is populated
- radar map panel is populated
- metrics show values
- detection table has rows

## Scenario 2: I Want To Trigger A Backend Run From The Dashboard

Use this when the dashboard should call the API directly.

Where:

- left sidebar, `Run via API`

Buttons and fields:

1. confirm `API base URL`
2. confirm `Scene JSON path`
3. confirm `Profile`
4. click `Run Scene on API`

Expected result:

- API run status changes from idle
- backend run is submitted
- after completion, output refresh is possible

## Scenario 3: I Want To Compare Two Runs

Use this when you already know the reference and candidate run IDs.

Where:

- left sidebar, `Compare Runs (API)`

Buttons and fields:

1. fill `Baseline ID`
2. fill `Reference run_id`
3. fill `Candidate run_id`
4. click `Compare`
5. click `Policy Verdict`

Expected result:

- compare status updates
- policy result is computed

## Scenario 4: I Want To Pin The Current Reference As Baseline

Use this before compare or policy evaluation.

Where:

- left sidebar, `Compare Runs (API)`

Buttons:

1. fill `Baseline ID`
2. fill `Reference run_id`
3. click `Pin Baseline`

Expected result:

- baseline pinning succeeds
- baseline state is ready for compare/policy

## Scenario 5: I Want To Run A Regression Session

Use this when you have several candidate runs to evaluate together.

Where:

- left sidebar, regression section

Buttons and fields:

1. fill `Regression Session ID`
2. fill `Candidate run_ids`
3. click `Run Regression Session`
4. click `Refresh History`

Expected result:

- session history is populated
- a session can be selected

## Scenario 6: I Want To Export A Session Or Review Package

Use this after a regression session exists.

Where:

- left sidebar, regression/export section

Buttons:

1. `Export Session`
2. `Review Bundle + Copy Path`
3. `Export Decision Report (.md)`

Expected result:

- export status lines update
- review bundle path appears when requested
- markdown decision report is generated

## Scenario 7: I Want To Tune Policy Before A Verdict

Use this when default thresholds are not enough.

Where:

- left sidebar, `Policy Tuning`

Buttons and fields:

1. choose a policy preset
2. adjust parity / fail-count / shape thresholds if needed
3. then click `Policy Verdict`

Expected result:

- verdict uses the current tuning values

## Scenario 8: I Want To Reuse History Instead Of Re-typing IDs

Use this when previous sessions/exports already exist.

Where:

- left sidebar, regression history section

Buttons and fields:

1. `Refresh History`
2. choose `Session History`
3. choose `Export History`
4. use `Export Session` or `Review Bundle + Copy Path`

Expected result:

- old session/export state is reused without re-entering everything

## Scenario 9: I Want To Read Failures Fast

Read in this order:

1. API health
2. API run status
3. compare status
4. regression/export status
5. only then the visual panels

Typical meanings:

| What you see | Meaning | What to do next |
| --- | --- | --- |
| API health not reachable | backend is down or wrong URL | fix API base URL or restart launcher |
| `Run Scene on API` fails | scene/profile/backend path problem | confirm scene path and rerun backend validator |
| compare fails | run IDs or baseline state are wrong | recheck reference/candidate IDs and pin baseline if needed |
| export/review bundle fails | session/export state is incomplete | refresh history and select a valid session first |

## Fast Decision Table

| If you want to... | Go to | Click first |
| --- | --- | --- |
| populate the dashboard | top left | `Refresh Outputs` |
| trigger a backend run | `Run via API` | `Run Scene on API` |
| compare two runs | `Compare Runs (API)` | `Compare` |
| compute the decision outcome | `Compare Runs (API)` | `Policy Verdict` |
| store a baseline | `Compare Runs (API)` | `Pin Baseline` |
| run a regression session | regression section | `Run Regression Session` |
| refresh selectable session/export history | regression section | `Refresh History` |
| export a session | regression/export section | `Export Session` |
| package a handoff bundle | regression/export section | `Review Bundle + Copy Path` |
| export markdown decision output | regression/export section | `Export Decision Report (.md)` |

## Related Documents

- [Frontend Dashboard Usage](116_frontend_dashboard_usage.md)
- [Classic Dashboard UX Manual](308_classic_dashboard_ux_manual.md)
- [Classic Dashboard Live Checklist](310_classic_dashboard_live_checklist.md)
- [Generated Reports Index](reports/README.md)
