# Frontend Document Map

## Purpose

Use this page when you know you need frontend documentation, but you do not yet know whether to start with `Graph Lab` or the `classic dashboard`.

This page is the top-level routing map for the frontend documentation set.

## Pick The UI First

| If you want... | Start with | Then open |
| --- | --- | --- |
| the main operator workbench with runtime selection, compare, artifact inspection, and decision export | [Graph Lab Document Map](322_graph_lab_doc_map.md) | [Graph Lab UX Manual](300_graph_lab_ux_manual.md) |
| the lightest demo/presentation dashboard with a simpler run-review flow | [Classic Dashboard Document Map](320_classic_dashboard_doc_map.md) | [Classic Dashboard UX Manual](308_classic_dashboard_ux_manual.md) |
| the shortest possible local frontend launch path before deciding | [Frontend Runtime Purpose Presets](280_frontend_runtime_purpose_presets.md) | one of the two document maps above |
| a one-page choice between the two UIs | this page | the map for the chosen UI |

## Choose By Task

| If you need to... | Open this first | Then open |
| --- | --- | --- |
| launch Graph Lab locally | [Graph Lab Document Map](322_graph_lab_doc_map.md) | [Graph Lab Live Checklist](306_graph_lab_live_checklist.md) |
| launch the classic dashboard locally | [Classic Dashboard Document Map](320_classic_dashboard_doc_map.md) | [Classic Dashboard Live Checklist](310_classic_dashboard_live_checklist.md) |
| compare low fidelity vs high fidelity | [Graph Lab Document Map](322_graph_lab_doc_map.md) | [Decision Pane Quick Guide](326_graph_lab_decision_pane_quick_guide.md) |
| inspect generated artifacts and compare evidence | [Graph Lab Document Map](322_graph_lab_doc_map.md) | [Artifact Inspector Quick Guide](304_artifact_inspector_quick_guide.md) |
| present a simpler dashboard view to another person | [Classic Dashboard Document Map](320_classic_dashboard_doc_map.md) | [Classic Dashboard UX Manual](308_classic_dashboard_ux_manual.md) |
| understand dashboard result/status boxes after a run | [Classic Dashboard Document Map](320_classic_dashboard_doc_map.md) | [Classic Dashboard Result And Evidence Quick Guide](314_classic_dashboard_result_evidence_quick_guide.md) |
| diagnose a Graph Lab failure | [Graph Lab Failure Reading Guide](324_graph_lab_failure_reading_guide.md) | [Graph Lab Live Checklist](306_graph_lab_live_checklist.md) |
| diagnose a classic dashboard failure | [Classic Dashboard Failure Reading Guide](316_classic_dashboard_failure_reading_guide.md) | [Classic Dashboard Live Checklist](310_classic_dashboard_live_checklist.md) |
| troubleshoot a frontend flow before picking a UI-specific guide | [Frontend Troubleshooting Map](330_frontend_troubleshooting_map.md) | the UI-specific failure guide |
| check which high-fidelity path is interactive right now | [graph_lab_high_fidelity_runtime_timing_latest.json](reports/graph_lab_high_fidelity_runtime_timing_latest.json) | [Graph Lab Document Map](322_graph_lab_doc_map.md) |

## Choose By Role

### Frontend Operator

Start with:

1. [Graph Lab Document Map](322_graph_lab_doc_map.md)
2. [Graph Lab Live Checklist](306_graph_lab_live_checklist.md)
3. [Artifact Inspector Quick Guide](304_artifact_inspector_quick_guide.md)

If the live flow is already failing, start instead with [Frontend Troubleshooting Map](330_frontend_troubleshooting_map.md).

Use this route when you are making runtime choices, compare decisions, and handoff briefs.

### Demo Or Presentation User

Start with:

1. [Classic Dashboard Document Map](320_classic_dashboard_doc_map.md)
2. [Classic Dashboard Live Checklist](310_classic_dashboard_live_checklist.md)
3. [Classic Dashboard Result And Evidence Quick Guide](314_classic_dashboard_result_evidence_quick_guide.md)

Use this route when you need the shortest viewer-oriented frontend path.

### Frontend Developer

Start with:

1. [Documentation Index](README.md)
2. [Graph Lab Document Map](322_graph_lab_doc_map.md)
3. [Classic Dashboard Document Map](320_classic_dashboard_doc_map.md)
4. [Generated Reports Index](reports/README.md)

Use this route when you need to decide which UI surface your change affects before running validators.

## Minimal Decision Rule

Use this rule:

- if you need runtime presets, compare history, artifact evidence, or decision export, choose `Graph Lab`
- if you need the lighter dashboard shell and a simpler review surface, choose the `classic dashboard`
- if you are still unsure, open the Graph Lab map first because it is the more capable frontend path

## Related Documents
- [Frontend Evidence Read Order By Role](334_frontend_evidence_read_order_by_role.md)

- [Frontend Evidence Map](332_frontend_evidence_map.md)
- [Frontend Troubleshooting Map](330_frontend_troubleshooting_map.md)
- [Documentation Index](README.md)
- [Generated Reports Index](reports/README.md)
- [Graph Lab Document Map](322_graph_lab_doc_map.md)
- [Classic Dashboard Document Map](320_classic_dashboard_doc_map.md)
