# Web E2E Graph Audit Scoped Quick-Apply + Operator Hints (M17.42)

## Goal

Reduce operator friction during deep-link restore by adding scope-specific quick apply actions and clearer restore/pin hints.

1. add one-click scoped quick apply actions for deep-link payload restore
2. keep existing restore-toggle apply behavior while sharing the same apply path
3. improve operator hints for effective restore scope and pin/chip state

Implementation:

- scoped quick-apply + operator hints:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- scoped quick-apply actions:
  - constants/helpers:
    - `FILTER_IMPORT_AUDIT_QUICK_APPLY_OPTIONS`
    - `resolveFilterImportAuditQuickApplyOption`
    - `applyFilterImportAuditDeepLinkBundleWithScopes`
    - `applyFilterImportAuditDeepLinkQuickScope`
  - UI keys:
    - `co_filter_import_audit_apply_quick_scopes`
    - `co_filter_import_audit_apply_quick_<id>`
    - `co_filter_import_audit_apply_quick_hint`
  - quick actions apply payload with explicit scope override and set restore tag as `quick:<id>`
- unified deep-link apply behavior:
  - `applyFilterImportAuditDeepLinkBundleFromText` delegates to scoped helper
  - parse/apply failure handling remains unchanged (`empty`, `parse`, `invalid payload`, `no restore scope`)
  - success status includes schema/scope/restore tag
- restore/pin operator hints:
  - keys:
    - `co_filter_import_audit_restore_scope_hint`
    - `co_filter_import_audit_pin_operator_hint`
  - restore hint shows effective toggle vector + active restore preset
  - pin hint shows pinned preset, active query preset, pin active/idle state, and chip filter mode

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8151 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8171
curl -s "http://127.0.0.1:8151/health"
curl -s "http://127.0.0.1:8171/frontend/graph_lab/panels.mjs" | rg -n "FILTER_IMPORT_AUDIT_QUICK_APPLY_OPTIONS|resolveFilterImportAuditQuickApplyOption|applyFilterImportAuditDeepLinkBundleWithScopes|applyFilterImportAuditDeepLinkQuickScope|co_filter_import_audit_apply_quick_scopes|co_filter_import_audit_apply_quick_|co_filter_import_audit_apply_quick_hint|co_filter_import_audit_restore_scope_hint|co_filter_import_audit_pin_operator_hint|quick apply overrides restore scope|restore:q"
```

Pass criteria:

1. backend regression remains pass
2. scoped quick-apply tokens are present
3. restore/pin operator hint tokens are present
4. deep-link apply path remains shared across default apply and quick apply
