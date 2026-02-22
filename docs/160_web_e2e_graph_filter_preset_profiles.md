# Web E2E Graph Filter Preset Profiles (M17.27)

## Goal

Make recurring triage scopes reusable via saved filter presets.

1. save current filter scope as a named preset
2. load/delete presets from overlay UI
3. persist presets safely across reloads with normalization

Implementation:

- filter preset storage + normalizer + UI controls:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- storage:
  - localStorage key: `graph_lab_contract_overlay_filter_presets_v1`
  - built-in presets:
    - `default`
    - `triage_hold_high`
- preset payload scope:
  - `sourceFilter`
  - `severityFilter`
  - `policyFilter`
  - `pinnedRunId`
  - `nonZeroOnly`
  - `gateHistoryLimit`
  - `gateHistoryPages`
  - `rowWindowSizeText`
- normalization:
  - name sanitizer: `normalizeFilterPresetName`
  - config sanitizer: `normalizeFilterPresetConfig`
  - invalid values clamped to safe/default ranges
- UI controls:
  - select: `co_filter_preset_select`
  - actions:
    - `Load Filter Preset`
    - `Save Filter Preset`
    - `Delete Filter Preset`
  - custom/built-in status hint: `preset: built-in|custom`
- preference persistence:
  - active preset and draft name are saved in overlay prefs and restored on reload

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8158 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8138
curl -s "http://127.0.0.1:8138/frontend/graph_lab/panels.mjs" | rg -n "CONTRACT_OVERLAY_FILTER_PRESETS_KEY|DEFAULT_FILTER_PRESETS|normalizeFilterPresetName|normalizeFilterPresetConfig|loadFilterPresets|saveFilterPresets|activeFilterPreset|filterPresetDraft|co_filter_preset_cfg|co_filter_preset_select|Load Filter Preset|Save Filter Preset|Delete Filter Preset|preset: built-in|preset: custom"
```

Pass criteria:

1. filter preset storage/normalization tokens are present
2. filter preset runtime/UI tokens are present
3. backend regression remains pass
