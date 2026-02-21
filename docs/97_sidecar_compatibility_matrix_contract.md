# Sidecar Compatibility Matrix Contract (M12.4)

## Goal

Lock parser behavior for strict/non-strict ingestion and ensure non-strict output still runs through bridge + scene pipeline.

## Matrix

1. strict mode + unknown top-level/object keys: must fail
2. non-strict mode + unknown top-level/object keys: must pass
3. non-strict manifest must preserve diagnostics:
   - `asset_parser_metadata.unknown_top_level_keys`
   - `asset_parser_metadata.unknown_object_keys`
4. non-strict manifest must remain bridge-compatible and produce canonical scene artifacts:
   - `path_list.json`
   - `adc_cube.npz`
   - `radar_map.npz`

## Validation Command

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sidecar_schema_compat_matrix.py
```

## Code Paths

- parser metadata diagnostics:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/scene_asset_parser.py`
- matrix validator:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sidecar_schema_compat_matrix.py`

## Acceptance

M12.4 is accepted only if matrix validation passes and strict/non-strict behavior is deterministic.
