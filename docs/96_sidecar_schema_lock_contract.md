# Sidecar Schema Lock Contract (M12.3)

## Goal

Lock sidecar schema profile/version and enforce strict parsing gate for deterministic ingestion.

## Defaults

- `schema_profile = "v1"`
- `schema_version = 1`
- strict mode: enabled by default in parser CLI

## Strict-Mode Rules

When strict mode is on:

1. top-level unknown keys are rejected
2. unknown object keys are rejected
3. profile/version mismatch is rejected

This prevents silent schema drift in sidecar inputs.

When strict mode is off:

1. unknown top-level keys are accepted and recorded
2. unknown object keys are accepted and recorded per object index
3. schema profile/version lock still applies unless explicitly changed by CLI options

## CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/build_asset_manifest_from_sidecar.py \
  --sidecar-json /path/to/scene_sidecar.json \
  --output-asset-manifest-json /path/to/asset_manifest.json \
  --profile v1 \
  --expected-sidecar-version 1 \
  --strict
```

Use `--non-strict` only for exploratory ingestion.
`--strict` and `--non-strict` are mutually exclusive.

## Code Paths

- constants + parser gate:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/scene_asset_parser.py`
- CLI wiring:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/build_asset_manifest_from_sidecar.py`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sidecar_asset_parser.py
```
