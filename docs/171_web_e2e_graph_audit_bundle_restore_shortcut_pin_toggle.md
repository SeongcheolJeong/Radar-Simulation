# Web E2E Graph Audit Bundle Restore + Shortcut Pin Toggle (M17.38)

## Goal

Speed up audit context restore and reduce repeated pointer travel for preset pinning.

1. restore audit query/page context from deep-link bundle JSON
2. expose restore status/validity in transfer area
3. add keyboard shortcut for pinned-preset toggle

Implementation:

- bundle restore + shortcut pin toggle:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- bundle restore parser/apply:
  - parser: `parseFilterImportAuditDeepLinkBundleText`
  - parsed payload state: `parsedFilterImportAuditDeepLinkPayload`
  - preview text: `filterImportAuditDeepLinkPreview`
  - apply callback: `applyFilterImportAuditDeepLinkBundleFromText`
  - UI keys:
    - `co_filter_import_audit_bundle_preview`
    - `co_filter_import_audit_apply_deeplink`
  - restore scope:
    - query: `search/kind/mode`
    - paging: `cap/offset`
    - pin state: `pinned_preset_id`
    - selected entry: `active_entry_id`
- shortcut quick toggle:
  - action id: `audit_pin_toggle`
  - default binding: `p`
  - execution path integrated via `triggerShortcutAction`
  - action target: `toggleFilterImportAuditPinnedPreset`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8149 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8169
curl -s "http://127.0.0.1:8149/health"
curl -s "http://127.0.0.1:8169/frontend/graph_lab/panels.mjs" | rg -n "audit_pin_toggle|parseFilterImportAuditDeepLinkBundleText|parsedFilterImportAuditDeepLinkPayload|filterImportAuditDeepLinkPreview|applyFilterImportAuditDeepLinkBundleFromText|co_filter_import_audit_apply_deeplink|co_filter_import_audit_bundle_preview|buildFilterImportAuditDeepLinkBundle|serializeFilterImportAuditDeepLinkBundle|copyFilterImportAuditDeepLinkBundle|toggleFilterImportAuditPinnedPreset"
```

Pass criteria:

1. backend regression remains pass
2. bundle restore parser/apply tokens are present
3. shortcut pin-toggle action tokens are present
