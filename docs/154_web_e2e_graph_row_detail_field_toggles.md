# Web E2E Graph Row Detail Field-Level Toggles (M17.21)

## Goal

Make row details operator-tunable so triage and deep-debug views can be switched without code changes.

1. choose which detail fields are rendered
2. provide quick presets for core vs full detail
3. keep persisted behavior stable across sessions

Implementation:

- row detail field-state model + renderer gating + overlay controls:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- detail field controls:
  - per-field checkboxes: `time`, `event/run`, `delta`, `snapshot`, `baseline`, `note_json`
  - selection counter shown as `selected n/6`
  - config block key: `co_detail_fields_cfg`
- quick presets:
  - `Core Fields` (time/event/delta only)
  - `All Fields` (all sections on)
  - existing overlay presets align with detail scope:
    - `Preset: Triage` -> core detail set
    - `Preset: Deep` -> all detail set
    - `Reset Preset` -> default detail set
- detail rendering gate:
  - `formatRowDetailText(row)` emits only selected sections
  - `note_json` serialization happens only when `note_json` field is selected
  - empty-selection guard keeps at least one section enabled
- persistence:
  - detail field selections persisted in overlay prefs via `detailFieldStates`

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8152 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8132
curl -s "http://127.0.0.1:8132/frontend/graph_lab/panels.mjs" | rg -n "DETAIL_FIELD_DEFS|DEFAULT_DETAIL_FIELD_STATES|detailFieldStates|applyDetailFieldPreset|toggleDetailField|co_detail_fields_cfg|Core Fields|All Fields|selected .*\\/|formatRowDetailText|detailFieldStates\\.timestamp_iso|detailFieldStates\\.event_meta|detailFieldStates\\.delta|detailFieldStates\\.snapshot|detailFieldStates\\.baseline|detailFieldStates\\.note_json"
```

Pass criteria:

1. detail field model/preset/control tokens are present
2. field-level renderer gating tokens are present
3. backend regression remains pass
