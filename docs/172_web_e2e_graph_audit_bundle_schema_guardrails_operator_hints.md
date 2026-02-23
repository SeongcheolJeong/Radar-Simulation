# Web E2E Graph Audit Bundle Schema Guardrails + Operator Hints (M17.39)

## Goal

Prevent invalid deep-link bundle restores and expose key operator context in UI.

1. enforce schema/kind guardrails for audit deep-link bundle restore
2. show explicit expected import contract in transfer area
3. show active audit preset and pin-toggle shortcut hint in controls

Implementation:

- schema guardrails + operator hints:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- bundle schema guardrails:
  - constants:
    - `FILTER_IMPORT_AUDIT_DEEPLINK_KIND`
    - `FILTER_IMPORT_AUDIT_DEEPLINK_SCHEMA_VERSION`
  - parser:
    - `parseFilterImportAuditDeepLinkBundleText`
  - validation rules:
    - `kind` must match deep-link bundle kind
    - `schema_version` must be present
    - unsupported `schema_version` rejected with explicit error
- bundle expectation hint:
  - key: `co_filter_import_audit_bundle_schema_hint`
  - text includes expected `kind/schema`
- preset/shortcut operator hints:
  - keys:
    - `co_filter_import_audit_preset_active_hint`
    - `co_filter_import_audit_shortcut_hint`
  - displays active preset id and current shortcut token for pin toggle

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8150 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8170
curl -s "http://127.0.0.1:8150/health"
curl -s "http://127.0.0.1:8170/frontend/graph_lab/panels.mjs" | rg -n "FILTER_IMPORT_AUDIT_DEEPLINK_KIND|FILTER_IMPORT_AUDIT_DEEPLINK_SCHEMA_VERSION|schema_version missing|unsupported schema_version|co_filter_import_audit_bundle_schema_hint|co_filter_import_audit_preset_active_hint|co_filter_import_audit_shortcut_hint|audit bundle expects kind=|pin shortcut:"
```

Pass criteria:

1. backend regression remains pass
2. deep-link schema guardrail tokens are present
3. operator hint tokens are present
