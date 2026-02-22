# Sionna PHY Runtime Sanity Contract (M14.3)

## Goal

Lock a minimal executable sanity check for the `sionna + tensorflow` runtime
track after environment provisioning.

## Scope

Validation script confirms:

1. `tensorflow` import and tensor op execution
2. `sionna` import
3. `sionna.phy.utils.ebnodb2no` numerical sanity value

## Code Path

- `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sionna_phy_runtime_minimal.py`

## Validation

Run in runtime venv:

```bash
PYTHONPATH=src /Users/seongcheoljeong/Documents/Codex_test/.venv-sionna311/bin/python \
  /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_sionna_phy_runtime_minimal.py
```

## Acceptance

M14.3 sanity is accepted only if:

1. script exits pass on runtime venv
2. tensor math and `ebnodb2no` output both match expected values
