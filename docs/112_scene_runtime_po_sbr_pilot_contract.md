# Scene Runtime PO-SBR Pilot Contract (M14.6)

## Goal

Add a first executable runtime pilot path for `po_sbr_rt` backend with deterministic
preflight gating for Linux+NVIDIA constraints.

## Scope

1. runtime provider:
   - load `POsolver.py` from PO-SBR repo
   - execute `build()` and `simulate()` and map output to canonical path payload
2. pilot runner:
   - preflight gate checks:
     - repo/geometry existence
     - required modules (`rtxpy`, `igl`)
     - platform (`Linux`)
     - NVIDIA runtime (`nvidia-smi`)
   - emit deterministic summary JSON in both states:
     - `pilot_status=executed`
     - `pilot_status=blocked` (`--allow-blocked`)
3. validation:
   - provider logic validation with stubbed solver
   - pilot summary contract validation (blocked/executed branches)
   - executed-summary hard gate validation (`pilot_status=executed`)

## Code Paths

- runtime provider:
  - `/Users/seongcheoljeong/Documents/Codex_test/src/avxsim/runtime_providers/po_sbr_rt_provider.py`
- pilot runner:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_po_sbr_pilot.py`
- validations:
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_po_sbr_runtime_provider_stubbed.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_runtime_po_sbr_provider_integration_stubbed.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_po_sbr_pilot.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_runtime_po_sbr_executed_report.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/validate_validate_scene_runtime_po_sbr_executed_report.py`
  - `/Users/seongcheoljeong/Documents/Codex_test/scripts/run_m14_6_po_sbr_linux_strict.sh`

## Validation

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_po_sbr_runtime_provider_stubbed.py
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_scene_runtime_po_sbr_provider_integration_stubbed.py
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_run_scene_runtime_po_sbr_pilot.py
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/validate_validate_scene_runtime_po_sbr_executed_report.py
```

Runtime pilot evidence run (current host may be blocked):

```bash
PYTHONPATH=src python3 /Users/seongcheoljeong/Documents/Codex_test/scripts/run_scene_runtime_po_sbr_pilot.py \
  --output-root /Users/seongcheoljeong/Documents/Codex_test/data/runtime_pilot/po_sbr_runtime_pilot_v1 \
  --output-summary-json /Users/seongcheoljeong/Documents/Codex_test/docs/reports/scene_runtime_po_sbr_pilot_m14_6_2026_02_22.json \
  --allow-blocked
```

## Acceptance

M14.6 is accepted only if:

1. provider emits canonical payload (`paths_by_chirp`) through runtime provider path
2. pilot runner emits deterministic summary with explicit `pilot_status`
3. blocked state includes deterministic blocker reasons and Linux rerun command
4. executed state records `runtime_resolution.mode=runtime_provider` with non-zero path count
5. executed report passes hard-gate validator (`validate_scene_runtime_po_sbr_executed_report.py`)
