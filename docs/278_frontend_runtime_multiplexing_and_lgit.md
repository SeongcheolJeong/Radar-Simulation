# Frontend Runtime Multiplexing + LGIT Output Guide

## Scope

This document describes the current Graph Lab runtime controls and output artifacts for:

- `radarsimpy_rt` runtime execution
- multiplexing controls (`tdm`, `bpm`, `custom`)
- LGIT customized output export

## Runtime Controls (Graph Lab)

In `Graph Inputs -> Runtime Config`:

- `Runtime Backend`: set to `radarsimpy_rt`
- `Simulation Mode`: use `radarsimpy_adc` for RadarSimPy ADC simulation path
- `Multiplexing Mode`: `tdm`, `bpm`, or `custom`
- `BPM Phase Code (deg)`: comma/newline-separated numbers
- `Multiplexing Plan JSON`: optional object payload for custom pulse matrices
- `License File`: absolute `.lic` path for production-tier runtime

Preset buttons are available:

- `Preset: TDM`
- `Preset: BPM 2TX`
- `Preset: Custom`

## Frontend -> Backend Runtime Payload

The frontend serializes runtime settings to:

```json
{
  "backend": {
    "type": "radarsimpy_rt",
    "runtime_input": {
      "simulation_mode": "radarsimpy_adc",
      "multiplexing_mode": "bpm",
      "bpm_phase_code_deg": [0, 180, 0, 180],
      "tx_multiplexing_plan": {
        "mode": "custom",
        "pulse_amp": [[1, 1], [1, 1]],
        "pulse_phs_deg": [[0, 0], [0, 180]]
      },
      "license_file": "/abs/path/license_RadarSimPy_*.lic"
    }
  }
}
```

Validation behavior:

- non-numeric BPM phase tokens are rejected
- invalid multiplexing mode is rejected
- malformed/non-object multiplexing JSON is rejected
- non-numeric `pulse_amp` / `pulse_phs_deg` containers are rejected

## Runtime Provider Behavior

`radarsimpy_rt_provider` resolves a multiplexing plan and writes:

- `pulse_amp` and `pulse_phs` into TX channel config
- runtime diagnostics into `provider_runtime_info`, including:
  - `multiplexing_mode`
  - `multiplexing_plan_source`
  - `active_tx_per_chirp`
  - pulse matrix shapes

## Concrete Runtime Examples

### TDM

Frontend inputs:

- Multiplexing Mode: `tdm`
- BPM Phase Code: empty
- Multiplexing Plan JSON: empty

Expected provider runtime info:

- `multiplexing_mode = "tdm"`
- `active_tx_per_chirp = [1, 1, ...]`
- `multiplexing_plan_source = "runtime_input"`

### BPM 2TX

Frontend inputs:

- Multiplexing Mode: `bpm`
- BPM Phase Code: `0,180,0,180`
- Multiplexing Plan JSON: empty

Expected provider runtime info:

- `multiplexing_mode = "bpm"`
- `active_tx_per_chirp = [2, 2, ...]`
- `pulse_amp_shape = [2, n_chirps]`
- `pulse_phs_deg_shape = [2, n_chirps]`

### Custom

Frontend inputs:

- Multiplexing Mode: `custom`
- Multiplexing Plan JSON:

```json
{
  "mode": "custom",
  "pulse_amp": [[1, 0.5, 1, 0.5], [0.5, 1, 0.5, 1]],
  "pulse_phs_deg": [[0, 45, 90, 135], [180, 225, 270, 315]]
}
```

Expected provider runtime info:

- `multiplexing_mode = "custom"`
- `multiplexing_plan_source = "runtime_input.tx_multiplexing_plan"`
- `active_tx_per_chirp = [2, 2, ...]`

## LGIT Output Artifact

Scene pipeline writes optional:

- `lgit_customized_output.npz`

Key arrays:

- `adc_virtual_scv`
- `range_doppler_power_drc`
- `tx_pair_doppler_power_pdr`
- `tx_pairs`
- `metadata_json`

This artifact is included in Graph Run summary output and cached artifact materialization.

Expected schema/shape (2TX/2RX, 4 chirps, 256 samples example):

- `adc_virtual_scv`: `[256, 4, 4]`
- `range_doppler_power_drc`: `[4, 128, 4]`
- `tx_pair_doppler_power_pdr`: `[2, 4, 128]`
- `tx_pairs`: `[2, 2]`
- `metadata_json.version = "lgit_customized_output_v1"`

## Production Runtime Command Baseline

If local runtime package is not globally installed, set package/lib paths:

```bash
export PYTHONPATH=src:external/radarsimpy_order_pull_latest/extracted/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU
export LD_LIBRARY_PATH=external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}
export RADARSIMPY_LICENSE_FILE=/home/seongcheoljeong/Documents/license_RadarSimPy_10760.lic
```

Then run production validation scripts (gate/readiness/parity).

## CI Template

A ready-to-run shell template is available:

```bash
scripts/run_radarsimpy_paid_6m_gate_ci.sh
```

The CI template also validates frontend-style runtime payload mapping to provider diagnostics:

- `scripts/validate_frontend_runtime_payload_provider_info_optional.py`
- report: `docs/reports/frontend_runtime_payload_provider_info_paid_6m.json`

Optional env overrides:

```bash
PY_BIN=.venv/bin/python \
RADARSIMPY_PACKAGE_ROOT=external/radarsimpy_order_pull_latest/extracted/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU \
RADARSIMPY_LIBCOMPAT_DIR=external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu \
RADARSIMPY_LICENSE_FILE=/home/seongcheoljeong/Documents/license_RadarSimPy_10760.lic \
REPORTS_ROOT=docs/reports \
scripts/run_radarsimpy_paid_6m_gate_ci.sh
```

## Troubleshooting

- `No module named 'radarsimpy'`:
  - set `PYTHONPATH` to extracted runtime package root.
- `ImportError: libmbedcrypto.so.7 not found`:
  - include libcompat directory in `LD_LIBRARY_PATH`.
  - ensure `libmbedcrypto.so.7` link resolves in that directory.
- `is_licensed` false:
  - ensure `.lic` path is valid and runtime invokes `set_license(...)`.
