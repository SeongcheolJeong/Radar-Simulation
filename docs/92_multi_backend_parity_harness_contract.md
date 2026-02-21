# Multi-Backend Parity Harness Contract (M11.4)

## Goal

Provide one command to compare radar-map parity between two object-scene backends.

Primary use:

- `hybrid_frames` vs `analytic_targets` on shared synthetic scenarios.

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_backend_parity.py \
  --reference-scene-json /path/to/reference_scene.json \
  --candidate-scene-json /path/to/candidate_scene.json \
  --output-root /path/to/parity_run \
  --output-summary-json /path/to/scene_backend_parity_summary.json \
  --allow-failures
```

## Workflow

1. Run `scene_json -> radar_map.npz` for reference scene.
2. Run `scene_json -> radar_map.npz` for candidate scene.
3. Compare `{fx_dop_win, fx_ang}` with parity metrics from `avxsim.parity`.
4. Emit parity summary JSON with backend types, map paths, metrics, failures.

## Output

Summary fields:

- `reference_backend_type`
- `candidate_backend_type`
- `reference_radar_map_npz`
- `candidate_radar_map_npz`
- `parity` (pass/metrics/failures/shape)

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_backend_parity.py
```
