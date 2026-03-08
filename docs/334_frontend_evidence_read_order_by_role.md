# Frontend Evidence Read Order By Role

## Purpose

Use this page when you already know you need frontend evidence, but you want the shortest report-reading order for your role.

This page does not explain the UI itself. It explains which current evidence files to open, in order, before you open manuals.

## Roles

| If you are... | Start here | Then open |
| --- | --- | --- |
| frontend operator using `Graph Lab` | `docs/reports/graph_lab_playwright_e2e_latest.json` | `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md` |
| demo or presentation user using the `classic dashboard` | `docs/reports/frontend_quickstart_v1.json` | `docs/reports/classic_dashboard_snapshots/latest/` |
| frontend developer validating a UI change | [Frontend Evidence Map](332_frontend_evidence_map.md) | the subsystem-specific read order below |
| validator checking current frontend health | `docs/reports/graph_lab_playwright_e2e_latest.json` | `docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json` |

## Read Order By Role

### Frontend Operator

Open these in order:

1. `docs/reports/graph_lab_playwright_e2e_latest.json`
2. `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md`
3. `docs/reports/graph_lab_playwright_snapshots/latest/`
4. `docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json`
5. `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json`

Use this order when you need to answer:

- did the current browser flow pass
- what did the current exported decision say
- what did the UI look like
- which high-fidelity path is interactive right now
- did the frontend/runtime contract drift

If this looks wrong, continue with:

- [Frontend Troubleshooting Map](330_frontend_troubleshooting_map.md)
- [Graph Lab Failure Reading Guide](324_graph_lab_failure_reading_guide.md)

### Demo Or Presentation User

Open these in order:

1. `docs/reports/frontend_quickstart_v1.json`
2. `docs/reports/classic_dashboard_snapshots/latest/dashboard_full.png`
3. `docs/reports/classic_dashboard_snapshots/latest/dashboard_full_annotated.png`
4. `docs/reports/classic_dashboard_snapshots/latest/dashboard_main_annotated.png`

Use this order when you need to answer:

- does the lightweight frontend path still launch cleanly
- what will another person actually see on the dashboard
- which result areas matter on the screen

If this looks wrong, continue with:

- [Frontend Troubleshooting Map](330_frontend_troubleshooting_map.md)
- [Classic Dashboard Failure Reading Guide](316_classic_dashboard_failure_reading_guide.md)

### Frontend Developer

Pick the changed surface first.

If you changed `Graph Lab`, open:

1. `docs/reports/graph_lab_playwright_e2e_latest.json`
2. `docs/reports/graph_lab_playwright_snapshots/latest/`
3. `docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json`
4. `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json`

If you changed the `classic dashboard`, open:

1. `docs/reports/frontend_quickstart_v1.json`
2. `docs/reports/classic_dashboard_snapshots/latest/`

If you changed shared frontend/backend runtime wiring, open:

1. `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json`
2. `docs/reports/frontend_runtime_payload_provider_info_paid_6m.json`
3. `docs/reports/graph_lab_playwright_e2e_latest.json`

Then use:

- [Generated Reports Index](reports/README.md)
- [Frontend Evidence Map](332_frontend_evidence_map.md)

### Frontend Validator

Open these in order:

1. `docs/reports/graph_lab_playwright_e2e_latest.json`
2. `docs/reports/graph_lab_high_fidelity_runtime_timing_latest.json`
3. `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json`
4. `docs/reports/frontend_quickstart_v1.json`
5. `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md`

Use this order when you need to answer:

- is the current frontend flow green
- is the current high-fidelity release story still valid
- is the runtime payload/provider contract still aligned
- is the lightweight dashboard path still usable

If one item fails, continue with:

- [Generated Reports Index](reports/README.md)
- [Frontend Troubleshooting Map](330_frontend_troubleshooting_map.md)

## Minimal Rule

Use this rule:

- start with `_latest.json`
- then open `latest/` snapshot directories or exported briefs
- only then open UX manuals for explanation

## Related Documents

- [Frontend Evidence Map](332_frontend_evidence_map.md)
- [Frontend Document Map](328_frontend_doc_map.md)
- [Frontend Troubleshooting Map](330_frontend_troubleshooting_map.md)
- [Generated Reports Index](reports/README.md)
