# Web E2E Graph Audit Deep-Link Bundle + Preset Pinning (M17.37)

## Goal

Improve audit handoff and repeated triage workflows.

1. copy a deep-link bundle for selected audit detail + query/page context
2. pin an audit query preset for repeat use
3. align reset behavior with pinned preset state

Implementation:

- deep-link bundle + preset pinning:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- deep-link bundle copy:
  - helpers:
    - `buildFilterImportAuditDeepLinkBundle`
    - `serializeFilterImportAuditDeepLinkBundle`
  - action callback:
    - `copyFilterImportAuditDeepLinkBundle`
  - UI key:
    - `co_filter_import_audit_copy_deeplink`
  - bundle payload contains:
    - active entry id/detail
    - current query (`search/kind/mode`)
    - current paging (`offset/cap/end`)
    - preset context (`active_preset_id`, `pinned_preset_id`)
- preset pinning:
  - resolver:
    - `resolveFilterImportAuditQueryPreset`
  - state:
    - `filterImportAuditPinnedPresetId`
  - derived state:
    - `filterImportAuditPresetPinnable`
    - `filterImportAuditPinnedPresetActive`
  - action callback:
    - `toggleFilterImportAuditPinnedPreset`
  - UI keys:
    - `co_filter_import_audit_preset_pin`
    - `co_filter_import_audit_preset_pin_hint`
- persistence/reset alignment:
  - overlay prefs include:
    - `filterImportAuditPinnedPreset`
  - `Reset Query` behavior:
    - if pinned preset exists, reset restores pinned preset (`audit query reset -> pinned:<id>`)
    - if not pinned, reset returns to `all/all/all`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8148 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8168
curl -s "http://127.0.0.1:8148/health"
curl -s "http://127.0.0.1:8168/frontend/graph_lab/panels.mjs" | rg -n "buildFilterImportAuditDeepLinkBundle|serializeFilterImportAuditDeepLinkBundle|copyFilterImportAuditDeepLinkBundle|resolveFilterImportAuditQueryPreset|filterImportAuditPinnedPresetId|filterImportAuditPinnedPresetActive|toggleFilterImportAuditPinnedPreset|filterImportAuditPresetPinnable|co_filter_import_audit_copy_deeplink|co_filter_import_audit_preset_pin|co_filter_import_audit_preset_pin_hint|filterImportAuditPinnedPreset|audit query preset pinned|audit query preset unpinned|audit query reset -> pinned"
```

Pass criteria:

1. backend regression remains pass
2. deep-link bundle copy tokens are present
3. preset pinning + pinned-reset behavior tokens are present
