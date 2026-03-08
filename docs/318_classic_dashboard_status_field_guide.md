# Classic Dashboard Status Field Guide

## Purpose

Use this guide when you can find the classic dashboard buttons, but you are not sure how to read the status lines and path boxes after pressing them.

Use it when you want to interpret:

- `api run status`
- `compare status`
- `regression status`
- `review bundle status`
- `decision report status`
- path/file boxes under export areas

If you need the full walkthrough, use [Classic Dashboard UX Manual](308_classic_dashboard_ux_manual.md).

If you need a failure-first reading flow, use [Classic Dashboard Failure Reading Guide](316_classic_dashboard_failure_reading_guide.md).

## Screen Reference

Control sidebar:

![Classic dashboard controls](reports/classic_dashboard_snapshots/latest/dashboard_controls.png)

Annotated status fields:

![Classic dashboard status fields annotated](reports/classic_dashboard_snapshots/latest/dashboard_controls_status_annotated.png)

## Read These Fields In Order

1. `api run status`
2. `compare status`
3. `regression status`
4. `regression downloads`
5. `review bundle status`
6. `review bundle path box`
7. `decision report status`
8. `decision report file box`

This order tells you whether the backend run worked, whether compare/regression completed, and whether export paths were actually produced.

## Status Field Meanings

### `api run status`

Use it after:

- `Run Scene on API`

Healthy if:

- it moves away from idle
- it reports a ready/completed state

Usually means trouble if:

- it stays idle after the button press
- it reports failure or an API-side error

## `compare status`

Use it after:

- `Compare`
- `Policy Verdict`

Healthy if:

- it moves away from idle
- it matches a populated `compare result box`

Usually means trouble if:

- it stays idle
- compare result stays `-`
- run IDs were missing or stale

## `regression status`

Use it after:

- `Run Regression Session`

Healthy if:

- it moves away from idle
- `Regression Gate` and history/export sections update after refresh

Usually means trouble if:

- candidate run IDs were malformed
- the session was created but history was not refreshed

## `regression downloads`

Use it after:

- `Export Session`

Healthy if:

- download paths or exported artifact references appear

Usually means trouble if:

- it remains `-`
- no valid session/export was selected first

## `review bundle status`

Use it after:

- `Review Bundle + Copy Path`

Healthy if:

- it changes away from idle
- it is paired with a non-empty path in the review bundle path box

Usually means trouble if:

- it stays idle
- the bundle path box stays `-`

## `review bundle path box`

Use it after:

- `Review Bundle + Copy Path`

Healthy if:

- it shows a concrete path
- the path changes when a newer bundle is built

Usually means trouble if:

- it stays `-`
- no valid export/session context existed before bundle generation

## `decision report status`

Use it after:

- `Export Decision Report (.md)`

Healthy if:

- it changes away from idle
- it pairs with a non-empty path in the decision report file box

Usually means trouble if:

- it stays idle
- the report file box stays empty or `-`

## `decision report file box`

Use it after:

- `Export Decision Report (.md)`

Healthy if:

- it shows a concrete markdown file path

Usually means trouble if:

- no report path was written
- the export was attempted before session/export context was ready

## Fast Read By Action

### After `Run Scene on API`

Read:

1. `api run status`
2. then header runtime badge
3. then visuals/metrics

### After `Compare`

Read:

1. `compare status`
2. `compare result box`

### After `Run Regression Session`

Read:

1. `regression status`
2. `Regression Gate`
3. `Session History`

### After `Export Session`

Read:

1. `regression downloads`
2. `Export History`

### After `Review Bundle + Copy Path`

Read:

1. `review bundle status`
2. `review bundle path box`

### After `Export Decision Report (.md)`

Read:

1. `decision report status`
2. `decision report file box`

## Fast Decision Table

| If you pressed | Read first | Healthy if | Usually wrong if not |
| --- | --- | --- | --- |
| `Run Scene on API` | `api run status` | moved away from idle | API/scene/profile/backend issue |
| `Compare` | `compare status` | non-idle and compare result exists | missing/stale run IDs |
| `Run Regression Session` | `regression status` | non-idle and history updates | malformed candidate IDs or stale history |
| `Export Session` | `regression downloads` | export references appear | no valid selected session/export |
| `Review Bundle + Copy Path` | `review bundle status` | path box becomes concrete | bundle/export context missing |
| `Export Decision Report (.md)` | `decision report status` | file box becomes concrete | report context missing |

## Related Documents

- [Classic Dashboard UX Manual](308_classic_dashboard_ux_manual.md)
- [Classic Dashboard Live Checklist](310_classic_dashboard_live_checklist.md)
- [Classic Dashboard Result And Evidence Quick Guide](314_classic_dashboard_result_evidence_quick_guide.md)
- [Classic Dashboard Failure Reading Guide](316_classic_dashboard_failure_reading_guide.md)
