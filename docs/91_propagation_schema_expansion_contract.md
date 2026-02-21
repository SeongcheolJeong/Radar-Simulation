# Propagation Schema Expansion Contract (M11.3)

## Goal

Expand canonical path metadata to improve path-level debugging and backend parity readiness.

Added fields:

- `path_id` (string)
- `material_tag` (string)
- `reflection_order` (int)

## Code Paths

- Path type:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/types.py`
- JSON writer:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/io.py`
- Hybrid frame adapter path metadata assignment:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/adapters/hybriddynamicrt_frames.py`
- Native analytic backend metadata assignment:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/scene_pipeline.py`

## Serialization Rules

- If metadata fields are available, include in `path_list.json`.
- Missing values remain omitted (backward compatible output).
- `reflection_order` is serialized as integer.

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_frame_adapter.py
```

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_to_radar_map.py
```

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_object_scene_analytic_backend.py
```
