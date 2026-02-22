# Web E2E Graph Overlay Shortcuts + Presets (M17.18)

## Goal

Speed up operator interaction by adding keyboard shortcuts and preset/reset actions in the contract overlay.

1. one-click preset switching for common workflows
2. keyboard-driven navigation/toggle in overlay
3. shortcut help visibility from UI

Implementation:

- overlay shortcut/preset logic:
  - `/Users/seongcheoljeong/Documents/Codex_test/frontend/graph_lab/panels.mjs`

## Behavior Contract

- preset actions:
  - `Preset: Triage`
  - `Preset: Deep`
  - `Reset Preset`
- shortcut toggle:
  - `Shortcuts: on/off` button
  - inline key help text when enabled
- keyboard map:
  - `h`: shortcut help toggle
  - `c`: compact toggle
  - `n`: non-zero toggle
  - `j`/`k`: next/prev row window
  - `g`: row window top
  - `1`/`2`/`0`: triage/deep/reset preset
- guard:
  - shortcuts are ignored while typing in editable targets (`input`, `textarea`, `select`, `contenteditable`)

## Validation

Backend regression:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_web_e2e_orchestrator_api.py
```

Frontend smoke:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_web_e2e_orchestrator_api.py --host 127.0.0.1 --port 8149 --repo-root /Users/seongcheoljeong/Documents/Codex_test --store-root /Users/seongcheoljeong/Documents/Codex_test/data/web_e2e
python3 -m http.server 8129
curl -s "http://127.0.0.1:8129/frontend/graph_lab/panels.mjs" | rg -n "Preset: Triage|Preset: Deep|Reset Preset|Shortcuts: on|Shortcuts: off|Shortcuts: h\\(|applyOverlayPreset|isEditableElementTarget|key === \\\"1\\\"|key === \\\"2\\\"|key === \\\"0\\\""
```

Pass criteria:

1. preset/reset UI tokens are present
2. keyboard shortcut map tokens are present
3. backend regression remains pass
