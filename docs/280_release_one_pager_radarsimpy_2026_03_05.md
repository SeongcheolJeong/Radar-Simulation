# One-Page Release Summary (External Share)

- Date: March 5, 2026
- Scope: RadarSimPy runtime integration + frontend multiplexing controls + production validation
- Reference detail doc: `docs/279_release_notes_radarsimpy_frontend_multiplexing_2026_03_05.md`

## Executive Outcome

This release moved the runtime path from TDM-focused behavior to multiplexing-aware execution (`tdm`, `bpm`, `custom`), exposed those controls in the frontend, and closed the paid-license production validation loop with passing gate reports.

## What Was Delivered

1. Runtime multiplexing generalization
- `radarsimpy_rt` now resolves and applies multiplexing plans with `pulse_amp` and `pulse_phs`.
- Runtime diagnostics now report selected mode and pulse-plan metadata.

2. Frontend controls for Radar Developer workflows
- New Graph Lab runtime inputs:
  - Multiplexing mode (`tdm|bpm|custom`)
  - BPM phase code
  - Multiplexing plan JSON
- Added quick presets:
  - `TDM`
  - `BPM 2TX`
  - `Custom`
- Added stronger input validation (mode/JSON/numeric checks).

3. LGIT-specific output adapter
- Added dedicated LGIT output module and generated artifact:
  - `lgit_customized_output.npz`
- Integrated into scene pipeline output and web summary artifact flow.

4. Production validation automation
- Added CI-ready execution template:
  - `scripts/run_radarsimpy_paid_6m_gate_ci.sh`
- Added targeted validators for runtime override contract and LGIT output schema.

## Validation Status (This Release)

All primary paid-runtime checks are green:

- Production release gate: `ready`
  - `docs/reports/radarsimpy_production_release_gate_paid_6m.json`
- Readiness checkpoint: `ready`
  - `docs/reports/radarsimpy_readiness_checkpoint_paid_6m.json`
- Simulator reference parity: `pass=true`
  - `docs/reports/radarsimpy_simulator_reference_parity_paid_6m.json`
- Graph Lab Playwright E2E: `pass`
  - `docs/reports/graph_lab_playwright_e2e_latest.json`

## Operational Requirements

For paid-runtime runs on hosts without global RadarSimPy installation:

```bash
export PYTHONPATH=src:external/radarsimpy_order_pull_latest/extracted/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU
export LD_LIBRARY_PATH=external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}
export RADARSIMPY_LICENSE_FILE=/home/seongcheoljeong/Documents/license_RadarSimPy_10760.lic
scripts/run_radarsimpy_paid_6m_gate_ci.sh
```

## Impact

- Development: faster and safer Radar runtime experiments via frontend presets + validation.
- Integration: stronger parity confidence through explicit runtime mode controls and report-backed gates.
- Delivery: reproducible production validation path now available as a single CI script.

