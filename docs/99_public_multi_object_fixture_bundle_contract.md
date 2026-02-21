# Public Multi-Object Fixture Bundle Contract (M12.6)

## Goal

Lock a deterministic replay bundle from a public asset with a multi-object layout preset.

## Scope

- onboarding runner with multi-object preset + bundle manifest:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_public_scene_asset_onboarding.py`
- deterministic validator (repeat run hash consistency):
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_public_multi_object_fixture_bundle.py`

## Required Behavior

1. `--object-layout-preset triple_lane` emits 3 objects in sidecar.
2. runner writes `replay_bundle_manifest.json` with:
   - object count
   - tx schedule/frame count
   - output artifact paths
   - artifact SHA256 hashes
3. re-running with same inputs keeps artifact hash set identical.

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_public_multi_object_fixture_bundle.py
```

## Real Public-Sample Run (Evidence)

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_public_scene_asset_onboarding.py \
  --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/scene_asset_onboarding/khronos_box_triple_lane_v1 \
  --asset-url https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Box/glTF-Binary/Box.glb \
  --asset-relative-path assets/Box.glb \
  --scene-id khronos_box_triple_lane_v1 \
  --object-layout-preset triple_lane \
  --strict \
  --summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/public_scene_asset_onboarding_khronos_box_triple_lane_v1_2026_02_21.json
```

## Acceptance

M12.6 is accepted only if deterministic validation passes and real public run summary is recorded.
