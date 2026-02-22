# Web E2E Graph Overlay Shortcut Remap + Profile Persistence (M17.20)

## Goal

Let operators remap overlay shortcuts without code edits, and persist/share key presets.

1. make every overlay action keybind editable
2. support shortcut profiles (load/save/delete/reset)
3. keep keyboard behavior deterministic with conflict visibility

Implementation:

- shortcut profile store + dynamic dispatch + remap UI:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- profile persistence:
  - localStorage key: `graph_lab_contract_overlay_shortcut_profiles_v1`
  - profile controls: `Load Profile`, `Save Profile`, `Delete Profile`, `Reset Keys`
  - built-in profiles: `default`, `ops_fast` (delete disabled for built-ins)
- dynamic key dispatch:
  - key->action map built from current bindings (`shortcutActionByKey`)
  - execution routed via `triggerShortcutAction(...)`
  - shortcut help text auto-renders current map (`shortcutHintText`)
- remap controls:
  - per-action single-key editor for all overlay actions (`SHORTCUT_ACTION_DEFS`)
  - key collisions surfaced inline (`dup`) and summary hint (`Shortcut conflict: ...`)
  - conflict rule is deterministic: first mapping wins
- prefs persistence extension:
  - overlay prefs now include active profile, draft name, and active binding map

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8151 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8131
curl -s "http://127.0.0.1:8131/frontend/graph_lab/panels.mjs" | rg -n "CONTRACT_OVERLAY_SHORTCUT_PROFILES_KEY|loadShortcutProfiles|saveShortcutProfiles|co_shortcut_profile_select|Load Profile|Save Profile|Delete Profile|Shortcut conflict|shortcutActionByKey|triggerShortcutAction|shortcutHintText|first mapping wins"
curl -s "http://127.0.0.1:8131/frontend/graph_lab_reactflow.html" | rg -n "contract-overlay-filter|contract-row-detail-btn|contract-overlay-row-detail"
```

Pass criteria:

1. shortcut profile/remap UI tokens are present
2. dynamic key-dispatch and hint-generation tokens are present
3. backend regression remains pass
