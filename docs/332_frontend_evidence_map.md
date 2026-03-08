# Frontend Evidence Map

## Purpose

Use this page when the frontend already ran and you now need to know which evidence files to open first.

This is the shortest routing page for frontend reports, snapshots, timing evidence, and exported briefs.

## Pick The UI First

| If your evidence question is about... | Open this first | Then open |
| --- | --- | --- |
| `Graph Lab` browser flow and current UI state | `docs/reports/graph_lab_playwright_e2e_latest.json` | `docs/reports/graph_lab_playwright_snapshots/latest/` |
| `Graph Lab` exported decision output | `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md` | `docs/reports/graph_lab_playwright_e2e_latest.json` |
| `Graph Lab` high-fidelity interactive path choice | `docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json` | [Graph Lab Document Map](322_graph_lab_doc_map.md) |
| `classic dashboard` quick demo/API path | `docs/reports/frontend_quickstart_v1.json` | [Classic Dashboard Document Map](320_classic_dashboard_doc_map.md) |
| frontend runtime payload/provider contract | `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json` | `docs/reports/frontend_runtime_payload_provider_info_paid_6m.json`, if paid runtime matters |

## Choose By Question

| If you need to answer... | Open this first | Then open |
| --- | --- | --- |
| does current Graph Lab browser E2E pass | `docs/reports/graph_lab_playwright_e2e_latest.json` | `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md` |
| what the current Graph Lab screen looked like | `docs/reports/graph_lab_playwright_snapshots/latest/page_full.png` | `docs/reports/graph_lab_playwright_snapshots/latest/page_full_annotated.png` |
| what the current decision/export output looked like | `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md` | `docs/reports/graph_lab_playwright_snapshots/latest/decision_pane.png` |
| whether `Sionna-style RT` or `PO-SBR` is the interactive high-fidelity path | `docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json` | `docs/reports/scene_backend_parity_sionna_rt_latest.json` and `docs/reports/scene_backend_parity_po_sbr_rt_latest.json` |
| whether the classic dashboard quick path still works | `docs/reports/frontend_quickstart_v1.json` | [Classic Dashboard Result And Evidence Quick Guide](314_classic_dashboard_result_evidence_quick_guide.md) |
| whether frontend/backend runtime payload wiring drifted | `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json` | `docs/reports/frontend_runtime_payload_provider_info_paid_6m.json` |

## Read Order By UI

### Graph Lab

1. `docs/reports/graph_lab_playwright_e2e_latest.json`
2. `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md`
3. `docs/reports/graph_lab_playwright_snapshots/latest/`
4. `docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json`
5. `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json`

Use this order when you need the current Graph Lab state, exported brief, screenshots, high-fidelity timing verdict, and contract evidence.

### Classic Dashboard

1. `docs/reports/frontend_quickstart_v1.json`
2. [Classic Dashboard Result And Evidence Quick Guide](314_classic_dashboard_result_evidence_quick_guide.md)
3. [Classic Dashboard Status Field Guide](318_classic_dashboard_status_field_guide.md)

Use this order when you only need the lightweight dashboard summary path.

## Minimal Evidence Rule

Use this rule:

- start with `_latest.json` when a current stable summary exists
- then open `latest/` snapshot directories for visual evidence
- only then move to UI manuals if you need explanation

## Related Documents
- [Frontend Evidence Read Order By Role](334_frontend_evidence_read_order_by_role.md)

- [Frontend Document Map](328_frontend_doc_map.md)
- [Frontend Troubleshooting Map](330_frontend_troubleshooting_map.md)
- [Generated Reports Index](reports/README.md)
- [Graph Lab Document Map](322_graph_lab_doc_map.md)
- [Classic Dashboard Document Map](320_classic_dashboard_doc_map.md)
