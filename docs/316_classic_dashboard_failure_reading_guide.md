# Classic Dashboard Failure Reading Guide

## Purpose

Use this guide when the classic dashboard is open, but one of the flows failed or looks stale.

Use it after:

- `Run Scene on API`
- `Compare`
- `Policy Verdict`
- `Run Regression Session`
- `Export Session`
- `Review Bundle + Copy Path`
- `Export Decision Report (.md)`

If you need the full screen walkthrough, use [Classic Dashboard UX Manual](308_classic_dashboard_ux_manual.md).

If you need the shortest click path first, use [Classic Dashboard Live Checklist](310_classic_dashboard_live_checklist.md).

## Screen Reference

Annotated full layout:

![Classic dashboard annotated](reports/classic_dashboard_snapshots/latest/dashboard_full_annotated.png)

Annotated main result area:

![Classic dashboard main annotated](reports/classic_dashboard_snapshots/latest/dashboard_main_annotated.png)

## Read Failures In This Order

1. header `runtime badge`
2. `api run status`
3. `compare status`
4. `regression status`
5. `compare result box`
6. `review bundle status`
7. `decision report status`
8. `Regression Gate`
9. `Decision Audit`
10. `Evidence Drill-Down`

Do not start from the big visuals first. Start from the status lines and path boxes.

## Failure Case 1: `Run Scene on API` Failed Or Looks Stale

Read:

1. `runtime badge`
2. `api run status`
3. `Scene JSON path`
4. `Profile`
5. then `Refresh Outputs`

Usually means:

- API server is unreachable
- scene path is wrong
- profile/backend path is invalid
- backend run did not finish before you inspected the dashboard

Fastest next action:

- verify `http://127.0.0.1:8099/health`
- rerun the launcher or [Frontend Dashboard Usage](116_frontend_dashboard_usage.md) flow

## Failure Case 2: Compare Produced No Useful Result

Read:

1. `compare status`
2. `compare result box`
3. `Reference run_id`
4. `Candidate run_id`
5. `Baseline ID`

Usually means:

- reference or candidate run ID is missing
- baseline/reference/candidate point to stale runs
- compare happened before the run finished

Fastest next action:

- confirm the run IDs came from a completed run
- rerun `Compare`
- then rerun `Policy Verdict`

## Failure Case 3: Policy Verdict Does Not Make Sense

Read:

1. `compare result box`
2. `Decision Audit`
3. `Evidence Drill-Down`
4. `Policy Tuning`

Usually means:

- compare data is stale
- policy preset or thresholds are not what you think
- the hot candidate is different from the one you were looking at

Fastest next action:

- re-read the `Decision Audit` summary and trend lines
- select the relevant candidate/rule in `Evidence Drill-Down`
- then run `Policy Verdict` again after tuning

## Failure Case 4: Regression Session Did Not Produce History

Read:

1. `regression status`
2. `Regression Gate`
3. `Session History`
4. `Export History`
5. `regression downloads`

Usually means:

- candidate run IDs were malformed
- history was not refreshed
- the session was created but you are still looking at stale history lists

Fastest next action:

- click `Refresh History`
- inspect `Regression Gate`
- rerun `Run Regression Session` with clean candidate IDs if needed

## Failure Case 5: Export Produced No Useful File Path

Read:

1. `review bundle status`
2. `review bundle path box`
3. `decision report status`
4. `decision report file box`
5. `regression downloads`

Usually means:

- no valid session/export was selected
- export was attempted before regression history was refreshed
- you are looking at an old selection state

Fastest next action:

- click `Refresh History`
- reselect `Session History` or `Export History`
- rerun the export action

## Failure Case 6: The Screen Looks Populated But You Still Do Not Trust It

Read:

1. `api run status`
2. `compare status`
3. `Regression Gate`
4. `Decision Audit`
5. `Evidence Drill-Down`
6. export path boxes

This usually means the dashboard is showing data, but you do not yet know whether it is fresh, compared, or exportable.

Fastest next action:

- rerun the matching checklist in [Classic Dashboard Live Checklist](310_classic_dashboard_live_checklist.md)
- then re-read the matching section in [Classic Dashboard Result And Evidence Quick Guide](314_classic_dashboard_result_evidence_quick_guide.md)

## Fast Decision Table

| If this failed | Read first | Usually wrong | Next action |
| --- | --- | --- | --- |
| API run | `api run status` | API/scene/profile path | rerun health check and API flow |
| compare | `compare status` | missing/stale run IDs | rerun compare after completed run |
| policy verdict | `Decision Audit` | stale compare or wrong preset | tune policy and rerun verdict |
| regression | `regression status` | malformed candidate IDs or stale history | refresh history and rerun session |
| export | export path boxes | no selected valid session/export | refresh history and rerun export |

## Related Documents

- [Frontend Dashboard Usage](116_frontend_dashboard_usage.md)
- [Classic Dashboard UX Manual](308_classic_dashboard_ux_manual.md)
- [Classic Dashboard Button Scenario Guide](312_classic_dashboard_button_scenario_guide.md)
- [Classic Dashboard Result And Evidence Quick Guide](314_classic_dashboard_result_evidence_quick_guide.md)
- [Classic Dashboard Live Checklist](310_classic_dashboard_live_checklist.md)
