# HybridDynamicRT Frame Adapter

## Purpose

Convert HybridDynamicRT Blender frame outputs into canonical `paths_by_chirp`.

## Supported Input Layout

Root example:

`<root>/Tx0Rx0/AmplitudeOutput0001.exr`
`<root>/Tx0Rx0/DistanceOutput0001.exr`

Scattering mode uses:

`<root>/Tx0Rx0/Depth0001.exr`

## API

Implemented in:

- `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/adapters/hybriddynamicrt_frames.py`

Main functions:

- `load_hybrid_paths_from_frames(...)`
- `load_hybrid_radar_geometry(...)`

## Mapping Rules

- Reflection mode:
  - `DistanceOutput` is interpreted as round-trip distance
  - delay is `tau = distance / c`
- Scattering mode:
  - `Depth` is interpreted as one-way depth
  - internally converted to round-trip distance by `*2`

## Angle Model

Pixel-to-angle mapping follows `fun_hybrid_pixel_angle.m` from HybridDynamicRT.

## Dependencies

- EXR/image read path uses `imageio` (`imageio.v3.imread`)
- For deterministic tests, `file_ext=".npy"` is supported

## Validation

Run:

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_hybrid_frame_adapter.py
```

