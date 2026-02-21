# Mock Measured Packs Contract

## Goal

Provide deterministic synthetic measured packs so the full replay-lock workflow can be exercised without external measured data.

## Generator CLI

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/generate_mock_measured_packs.py \
  --output-root /tmp/mock_measured_packs
```

Optional:

- `--include-failing-pack` (inject failing candidate)
- `--seed` (default `7`)

Generated per-pack files:

- `scenario_profile.json`
- `reference_estimation.npz`
- `candidates/*.npz`
- `lock_policy.json`
- `replay_manifest.json`

## End-to-End Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_mock_measured_packs_e2e.py
```

Validation covers:

- all-pass pack set -> overall lock pass
- failing pack set -> strict mode exit code `2`
