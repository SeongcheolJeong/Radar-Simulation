# Public Scene Asset Onboarding Contract (M12.5)

## Goal

Lock a reproducible onboarding path from a public glTF/OBJ asset into:

1. sidecar (`schema_profile/version`)
2. asset manifest
3. mesh scene JSON
4. canonical radar outputs (`path_list`, `adc_cube`, `radar_map`)

## Scope

- onboarding runner:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_public_scene_asset_onboarding.py`
- offline validator (no network dependency):
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_public_scene_asset_onboarding.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_public_scene_asset_onboarding.py
```

## Real Public-Sample Run (Evidence)

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_public_scene_asset_onboarding.py \
  --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/scene_asset_onboarding/khronos_box_v1 \
  --asset-url https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Box/glTF-Binary/Box.glb \
  --asset-relative-path assets/Box.glb \
  --scene-id khronos_box_v1 \
  --strict \
  --summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/public_scene_asset_onboarding_khronos_box_v1_2026_02_21.json
```

## Acceptance

M12.5 is accepted only if:

1. validator passes with local source-path fixture
2. one real public asset run succeeds and summary JSON is recorded with asset hash and output artifact paths
