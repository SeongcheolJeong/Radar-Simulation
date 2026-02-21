# Public OBJ Mixed-Format Matrix Contract (M12.7)

## Goal

Lock OBJ onboarding parity and mixed-format (`glTF + OBJ`) fixture matrix behavior.

## Scope

- mixed-format validator:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_public_mixed_format_fixture_matrix.py`
- shared onboarding runner:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_public_scene_asset_onboarding.py`

## Required Behavior

1. local mixed-format matrix validation passes:
   - `.glb` fixture maps to `source_mesh_format=gltf`
   - `.obj` fixture maps to `source_mesh_format=obj`
2. both formats produce canonical outputs (`path_list`, `adc_cube`, `radar_map`)
3. at least one real public OBJ run is recorded with summary evidence

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_public_mixed_format_fixture_matrix.py
```

## Real Public OBJ Run (Evidence)

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_public_scene_asset_onboarding.py \
  --output-root /Users/seongcheoljeong/Documents/Codex_test/data/public/scene_asset_onboarding/walthead_obj_v1 \
  --asset-url https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/obj/walt/WaltHead.obj \
  --asset-relative-path assets/WaltHead.obj \
  --scene-id walthead_obj_v1 \
  --object-layout-preset single \
  --strict \
  --summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/public_scene_asset_onboarding_walthead_obj_v1_2026_02_21.json
```

## Acceptance

M12.7 is accepted only if mixed-format validation passes and OBJ summary evidence is recorded.
