# Web E2E Graph Shortcut Profile Transfer Import/Export (M17.22)

## Goal

Enable team-shareable shortcut profile workflows without touching source code.

1. export current shortcut profiles as versioned JSON
2. import profiles from shared JSON and normalize safely
3. provide overlay-native transfer controls for copy/load/apply

Implementation:

- shortcut transfer bundle/parser/actions/UI:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- export bundle format:
  - `schema_version`
  - `kind` = `graph_lab_contract_overlay_shortcut_profiles`
  - `exported_at_iso`
  - `profiles` (normalized action-key map per profile)
- transfer controls:
  - `Export Profiles` (file download + text buffer fill)
  - `Copy Profiles` (clipboard write when available)
  - `Load JSON` (file picker -> text buffer)
  - `Import Profiles` (parse + merge into current profile set)
- parser behavior:
  - accepts either bundle form (`{..., "profiles": {...}}`) or direct profile-map form
  - ignores invalid entries and rejects payload with no valid profiles
  - normalizes profile names (`normalizeShortcutProfileName`) and bindings (`normalizeShortcutBindings`)
- operator feedback:
  - transfer editor textarea: `co_shortcut_transfer_text`
  - status line: `co_shortcut_transfer_status`
  - explicit import failure status (`import failed: ...`)

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8153 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8133
curl -s "http://127.0.0.1:8133/frontend/graph_lab/panels.mjs" | rg -n "buildShortcutProfileExportBundle|serializeShortcutProfileExportBundle|parseShortcutProfileImportText|co_shortcut_transfer_cfg|Export Profiles|Copy Profiles|Load JSON|Import Profiles|co_shortcut_transfer_text|co_shortcut_transfer_status|schema_version|graph_lab_contract_overlay_shortcut_profiles"
```

Pass criteria:

1. transfer bundle/parser/action tokens are present
2. overlay transfer UI/status tokens are present
3. backend regression remains pass
