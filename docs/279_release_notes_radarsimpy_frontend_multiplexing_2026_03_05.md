# Release Notes: RadarSimPy Runtime + Frontend Multiplexing

- Release date (KST): March 5, 2026
- Base commit: `c06121183ca9a10ee6e49bc31365b7b9fc592823`
- Included commits:
  - `853153d3c2c6188989ea49300a3b5b6828385ec5`
  - `52dda6454e4c6ec2e84e89b24e4a9cde620ab91e`

## Summary

This release delivers:

1. Runtime multiplexing generalization (`tdm`, `bpm`, `custom`) for `radarsimpy_rt`.
2. Frontend controls and validation for BPM/custom runtime inputs.
3. Dedicated LGIT output adapter (`lgit_customized_output.npz`) integrated in scene + web summary flow.
4. Paid 6-month production gate CI template and validated report outputs.
5. Additional checkpoint/report artifacts and architecture reference asset updates.

## Functional Changes

### 1) Runtime provider: multiplexing-aware TX plan

- File: `src/avxsim/runtime_providers/radarsimpy_rt_provider.py`
- Added runtime multiplexing plan resolution:
  - `runtime_input.multiplexing_mode`: `tdm|bpm|custom`
  - `runtime_input.bpm_phase_code_deg`
  - `runtime_input.tx_multiplexing_plan`
  - optional direct matrices (`tx_pulse_amp`, `tx_pulse_phs_deg`)
- TX channel construction now passes both:
  - `pulse_amp`
  - `pulse_phs`
- Runtime diagnostics now include:
  - `multiplexing_mode`
  - `multiplexing_plan_source`
  - `active_tx_per_chirp`
  - pulse matrix shapes

### 2) Frontend: runtime multiplexing controls + payload validation

- Files:
  - `frontend/graph_lab/app.mjs`
  - `frontend/graph_lab/contracts.mjs`
  - `frontend/graph_lab/panels.mjs`
  - `frontend/graph_lab/panels/runtime.mjs`
  - `frontend/graph_lab/hooks/use_graph_run_ops.mjs`
  - `frontend/graph_lab/runtime_overrides.mjs` (new)
- Added runtime UI fields:
  - Multiplexing mode
  - BPM phase code text
  - Multiplexing plan JSON
- Added preset actions:
  - `Preset: TDM`
  - `Preset: BPM 2TX`
  - `Preset: Custom`
- Added strict frontend-side validation:
  - invalid mode rejection
  - non-numeric BPM token rejection
  - invalid JSON/object rejection
  - non-numeric nested matrix payload rejection

### 3) LGIT adapter and artifact propagation

- New file: `src/avxsim/lgit_output_adapter.py`
- Integrated in:
  - `src/avxsim/scene_pipeline.py`
  - `src/avxsim/web_e2e_api.py`
- New optional output artifact:
  - `lgit_customized_output.npz`
- Included in graph-run output summary and cache artifact materialization.

### 4) CI template and validators

- New script:
  - `scripts/run_radarsimpy_paid_6m_gate_ci.sh`
- New validators:
  - `scripts/validate_graph_lab_runtime_overrides.mjs`
  - `scripts/validate_lgit_output_adapter.py`

### 5) Documentation updates

- `docs/03_architecture.md`: TDM-only wording updated to multiplexing-aware synthesizer model.
- `docs/Frontendref.md`: points to current authoritative runtime guide.
- New guide:
  - `docs/278_frontend_runtime_multiplexing_and_lgit.md`
- Added architecture image asset:
  - `docs/architecture.png`

## Verification and Gate Results

Validated in this release window:

- `docs/reports/radarsimpy_production_release_gate_paid_6m.json`
  - `production_gate_status = ready`
- `docs/reports/radarsimpy_readiness_checkpoint_paid_6m.json`
  - `overall_status = ready`
- `docs/reports/radarsimpy_simulator_reference_parity_paid_6m.json`
  - `pass = true`, `runtime_available = true`
- Playwright graph lab E2E:
  - `docs/reports/graph_lab_playwright_e2e_latest.json` (`pass`)

Additional checkpoint/parity artifacts from the same execution track were committed for traceability.

## Runtime Requirements (for paid-runtime execution)

When runtime package is not globally installed, set:

```bash
export PYTHONPATH=src:external/radarsimpy_order_pull_latest/extracted/Ubuntu24_x86_64_CPU/Ubuntu24_x86_64_CPU
export LD_LIBRARY_PATH=external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}
export RADARSIMPY_LICENSE_FILE=/home/seongcheoljeong/Documents/license_RadarSimPy_10760.lic
```

Then run:

```bash
scripts/run_radarsimpy_paid_6m_gate_ci.sh
```

## Notes / Known Constraints

- The runtime package import can fail without `LD_LIBRARY_PATH`/libcompat wiring.
- The simulator parity path may print an initial free-tier banner before explicit `set_license(...)`; final license state is validated in reports.
- Report/snapshot retention policy automation is available:
  - `scripts/run_radarsimpy_report_retention_audit.sh`
  - `docs/283_radarsimpy_report_retention_policy_2026_03_05.md`
  - `.github/workflows/radarsimpy-report-retention-audit.yml`
