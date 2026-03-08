# Frontend Troubleshooting Map

## Purpose

Use this page when a frontend flow looks wrong, blocked, stale, or failed, and you need to know which troubleshooting document to open first.

This is the shortest routing page for frontend failure diagnosis across both `Graph Lab` and the `classic dashboard`.

## Start With The Right UI

| If the problem is in... | Open this first | Then open |
| --- | --- | --- |
| `Graph Lab` | [Graph Lab Failure Reading Guide](324_graph_lab_failure_reading_guide.md) | [Graph Lab Live Checklist](306_graph_lab_live_checklist.md) |
| `classic dashboard` | [Classic Dashboard Failure Reading Guide](316_classic_dashboard_failure_reading_guide.md) | [Classic Dashboard Live Checklist](310_classic_dashboard_live_checklist.md) |
| you are not sure which UI is the right one | [Frontend Document Map](328_frontend_doc_map.md) | the UI-specific failure guide |

## Start With The Symptom

| If you see... | Open this first | Then check |
| --- | --- | --- |
| Graph Lab `Run Graph (API)` failed | [Graph Lab Failure Reading Guide](324_graph_lab_failure_reading_guide.md) | [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md) |
| Graph Lab compare/gate/export flow is blocked | [Decision Pane Quick Guide](326_graph_lab_decision_pane_quick_guide.md) | [Graph Lab Failure Reading Guide](324_graph_lab_failure_reading_guide.md) |
| Graph Lab artifacts look missing or strange | [Artifact Inspector Quick Guide](304_artifact_inspector_quick_guide.md) | [Graph Lab Failure Reading Guide](324_graph_lab_failure_reading_guide.md) |
| classic dashboard run looks stale or empty | [Classic Dashboard Failure Reading Guide](316_classic_dashboard_failure_reading_guide.md) | [Frontend Dashboard Usage](116_frontend_dashboard_usage.md) |
| classic dashboard status lines are confusing | [Classic Dashboard Status Field Guide](318_classic_dashboard_status_field_guide.md) | [Classic Dashboard Failure Reading Guide](316_classic_dashboard_failure_reading_guide.md) |
| classic dashboard result panels look populated but untrustworthy | [Classic Dashboard Result And Evidence Quick Guide](314_classic_dashboard_result_evidence_quick_guide.md) | [Classic Dashboard Failure Reading Guide](316_classic_dashboard_failure_reading_guide.md) |
| the chosen high-fidelity path may be the problem | [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json) | [Graph Lab Document Map](322_graph_lab_doc_map.md) |

## Fastest Diagnostic Rule

Use this rule:

1. choose the UI first
2. read the failure guide for that UI
3. then read the shortest checklist for that same UI
4. only after that, open field-level or panel-level guides

This avoids mixing up launch problems, compare-state problems, and evidence-reading problems.

## Diagnostic Order By UI

### Graph Lab

1. [Graph Lab Failure Reading Guide](324_graph_lab_failure_reading_guide.md)
2. [Graph Lab Live Checklist](306_graph_lab_live_checklist.md)
3. [Decision Pane Quick Guide](326_graph_lab_decision_pane_quick_guide.md)
4. [Artifact Inspector Quick Guide](304_artifact_inspector_quick_guide.md)
5. [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json), if the issue is specifically high-fidelity path choice

### Classic Dashboard

1. [Classic Dashboard Failure Reading Guide](316_classic_dashboard_failure_reading_guide.md)
2. [Classic Dashboard Live Checklist](310_classic_dashboard_live_checklist.md)
3. [Classic Dashboard Status Field Guide](318_classic_dashboard_status_field_guide.md)
4. [Classic Dashboard Result And Evidence Quick Guide](314_classic_dashboard_result_evidence_quick_guide.md)

## What Not To Do First

Do not start with:

- screenshots only
- export paths only
- artifact absence only
- policy verdict only

Start with the run/failure guide for the active UI first.

## Related Documents
- [Frontend Documentation Freeze Note](336_frontend_doc_chain_freeze_note_2026_03_08.md)

- [Frontend Document Map](328_frontend_doc_map.md)
- [Graph Lab Document Map](322_graph_lab_doc_map.md)
- [Classic Dashboard Document Map](320_classic_dashboard_doc_map.md)
- [Documentation Index](README.md)
- [Generated Reports Index](reports/README.md)
