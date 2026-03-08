# Frontend Documentation Freeze Note

- Date: March 8, 2026
- Status: active for the current frontend/operator release cut

## Purpose

This note freezes the current frontend documentation and evidence-routing chain so future updates stay focused on evidence refresh, UI behavior changes, and troubleshooting accuracy.

Do not keep creating new parallel frontend overview docs for the same cut.

## Authoritative Frontend Document Chain

Use this chain in order:

1. [Frontend Document Map](328_frontend_doc_map.md)
2. [Frontend Evidence Map](332_frontend_evidence_map.md)
3. [Frontend Evidence Read Order By Role](334_frontend_evidence_read_order_by_role.md)
4. [Frontend Troubleshooting Map](330_frontend_troubleshooting_map.md)
5. [Generated Reports Index](reports/README.md)

Then move into the UI-specific branch only when needed:

- `Graph Lab`: [Graph Lab Document Map](322_graph_lab_doc_map.md)
- `classic dashboard`: [Classic Dashboard Document Map](320_classic_dashboard_doc_map.md)

## Default Maintenance Rule

Do not add new frontend summary or routing docs for this cut unless one of the update triggers below is true.

Prefer:

- refreshing frontend evidence
- updating the existing frontend maps and guides
- correcting links, routing, or wording inside the frozen chain
- updating UI-specific manuals only when the UI behavior actually changes

## Allowed Update Triggers

Update the frozen frontend chain only when:

- the `Graph Lab` operator flow changes in a meaningful way
- the `classic dashboard` flow changes in a meaningful way
- the stable frontend evidence set changes
- the high-fidelity interactive frontend story changes
- the troubleshooting decision path changes
- a current document in the frozen chain becomes misleading or stale

## Non-Trigger Changes

Do not create new frontend overview docs only for:

- wording-only variants
- alternate summaries with the same routing meaning
- duplicate EN/KO overview pages outside the frozen chain
- small rearrangements that do not change operator decisions

## Operator Rule

For the current cut:

- start with the frozen chain above
- refresh evidence before adding explanation
- prefer `_latest.json` and `latest/` snapshots before opening long manuals
- reopen the chain only if the UI story or evidence story actually changed
