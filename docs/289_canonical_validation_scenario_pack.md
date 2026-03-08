# Canonical Validation Scenario Pack

## Purpose

This document defines the fixed validation scenario pack to use before release-candidate closure.

Use it to answer four questions in a repeatable order:

1. Does the frontend/operator workflow still work?
2. Does the low-fidelity RadarSimPy path still behave correctly?
3. Do the high-fidelity backends still satisfy their contract/parity checks?
4. Does the paid RadarSimPy production path still pass end-to-end?

One-command runner:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_canonical_release_candidate_subset.py \
  --output-json docs/reports/canonical_release_candidate_subset_latest.json
```

- Korean version: [정식 검증 시나리오 팩](290_canonical_validation_scenario_pack_ko.md)

## How To Use This Pack

- run from the repository root
- keep `PYTHONPATH=src`
- use the scenario subsets that match the runtimes you actually have installed
- prefer the output paths below so the reports stay easy to find
- use [Generated Reports Index](reports/README.md) to interpret the resulting evidence

## Scenario Matrix

| Scenario ID | Goal | Minimum prerequisite | Primary command | Persistent evidence |
| --- | --- | --- | --- | --- |
| `FE-1` | Graph Lab browser/operator flow | `.venv`, Playwright browsers | `scripts/validate_graph_lab_playwright_e2e.py` | `graph_lab_playwright_e2e_latest.json`, `graph_lab_playwright_snapshots/latest/`, `frontend_quickstart_v1.json` |
| `FE-2` | frontend runtime payload -> provider info contract | `.venv`, local RadarSimPy runtime assets | `scripts/validate_frontend_runtime_payload_provider_info_optional.py --require-runtime` | `frontend_runtime_payload_provider_info_optional_latest.json` |
| `RS-1` | trial-runtime layered parity | `.venv`, RadarSimPy trial bundle | `scripts/run_radarsimpy_layered_parity_suite.py --require-runtime-trial` | `radarsimpy_layered_parity_suite_trial_latest.json`, `radarsimpy_layered_parity_trial_latest.json` |
| `HF-1` | Sionna-style RT parity contract | `.venv` or `.venv-sionna311` | `scripts/run_scene_backend_parity_sionna_rt.py` | `scene_backend_parity_sionna_rt_latest.json` |
| `HF-2` | PO-SBR parity/readiness path | `.venv` or `.venv-po-sbr` | `scripts/run_scene_backend_parity_po_sbr_rt.py`, `scripts/run_po_sbr_post_change_gate.py --strict` | `scene_backend_parity_po_sbr_rt_latest.json`, `po_sbr_post_change_gate_*.json`, optional `po_sbr_progress_snapshot_manual.json` |
| `RS-2` | paid RadarSimPy production closure | `.venv`, paid `.lic`, runtime bundle | `scripts/run_radarsimpy_paid_6m_gate_ci.sh` | `radarsimpy_*_paid_6m.json`, `frontend_runtime_payload_provider_info_paid_6m.json` |

## Recommended Order

Run the pack in this order:

1. `FE-1`
2. `FE-2`
3. `RS-1`
4. `HF-1`
5. `HF-2`
6. `RS-2`

This order moves from cheapest/high-signal checks to heavier runtime and paid-license checks.

## Scenario Details

### FE-1: Graph Lab Browser Flow

Use this when:

- you changed `frontend/graph_lab`
- you changed web/API orchestration
- you need operator-level confidence, not just API health

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_web_e2e_orchestrator_api.py
PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers PYTHONPATH=src .venv/bin/python \
  scripts/validate_graph_lab_playwright_e2e.py \
  --require-playwright \
  --output-json docs/reports/graph_lab_playwright_e2e_latest.json
```

Expect:

- `docs/reports/graph_lab_playwright_e2e_latest.json`
- `docs/reports/graph_lab_playwright_snapshots/latest/decision_brief.md`
- `docs/reports/graph_lab_playwright_snapshots/latest/page_full.png`

Pass means:

- the browser flow is still operable
- compare workflow still renders
- current exported decision brief still matches the live UI state

### FE-2: Frontend Runtime Contract

Use this when:

- you changed runtime preset wiring
- you changed multiplexing/BPM/custom payload generation
- you need proof that frontend intent still reaches `radarsimpy_rt` provider info

Run:

```bash
PYTHONPATH=src .venv/bin/python \
  scripts/validate_frontend_runtime_payload_provider_info_optional.py \
  --require-runtime \
  --output-json docs/reports/frontend_runtime_payload_provider_info_optional_latest.json
```

Expect:

- `docs/reports/frontend_runtime_payload_provider_info_optional_latest.json`

Pass means:

- frontend `tdm`, `bpm`, and `custom` runtime inputs still map to the expected provider-side multiplexing fields

### RS-1: Trial Runtime Layered Parity

Use this when:

- you changed RadarSimPy wrapper/runtime coupling
- you changed white-box vs black-box comparison logic
- you need the lowest-cost runtime-backed parity scenario before the paid path

Run:

```bash
PYTHONPATH=src .venv/bin/python \
  scripts/run_radarsimpy_layered_parity_suite.py \
  --output-json docs/reports/radarsimpy_layered_parity_suite_trial_latest.json \
  --trial-output-json docs/reports/radarsimpy_layered_parity_trial_latest.json \
  --require-runtime-trial
```

Expect:

- `docs/reports/radarsimpy_layered_parity_suite_trial_latest.json`
- `docs/reports/radarsimpy_layered_parity_trial_latest.json`

Pass means:

- the trial-runtime white-box vs RadarSimPy black-box layered parity path still holds
- the repo can still use the local trial runtime bundle without paid-license-only features

### HF-1: Sionna-Style RT Parity Contract

Use this when:

- you changed `sionna_rt` backend handling
- you changed scene-backend parity logic
- you need a deterministic candidate-vs-reference parity check for the Sionna-style path

Run:

```bash
PYTHONPATH=src .venv/bin/python \
  scripts/run_scene_backend_parity_sionna_rt.py \
  --output-json docs/reports/scene_backend_parity_sionna_rt_latest.json
```

Expect:

- `docs/reports/scene_backend_parity_sionna_rt_latest.json`

Pass means:

- the analytic reference scene and the `sionna_rt` candidate scene still satisfy the current parity contract

### HF-2: PO-SBR Parity And Readiness

Use this when:

- you changed `po_sbr_rt` backend handling
- you changed runtime-affecting PO-SBR code
- you need both candidate-vs-reference parity and readiness/closure status

Run:

```bash
PYTHONPATH=src .venv/bin/python \
  scripts/run_scene_backend_parity_po_sbr_rt.py \
  --output-json docs/reports/scene_backend_parity_po_sbr_rt_latest.json
PYTHONPATH=src .venv/bin/python scripts/run_po_sbr_post_change_gate.py --strict
PYTHONPATH=src .venv/bin/python \
  scripts/show_po_sbr_progress.py \
  --strict-ready \
  --output-json docs/reports/po_sbr_progress_snapshot_manual.json
```

Expect:

- `docs/reports/scene_backend_parity_po_sbr_rt_latest.json`
- `docs/reports/po_sbr_progress_snapshot_manual.json`
- latest `docs/reports/po_sbr_post_change_gate_*.json`

Pass means:

- the PO-SBR candidate scene still satisfies the analytic-reference parity contract
- the runtime-affecting readiness gate is still green
- current closure/progress state is still ready

### RS-2: Paid RadarSimPy Production Closure

Use this when:

- you need release-facing RadarSimPy evidence
- you have the paid `.lic` and runtime assets
- you are closing the production path, not just the trial path

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_radarsimpy_paid_6m_gate_ci.sh
```

Expect:

- `docs/reports/radarsimpy_production_release_gate_paid_6m.json`
- `docs/reports/radarsimpy_readiness_checkpoint_paid_6m.json`
- `docs/reports/radarsimpy_simulator_reference_parity_paid_6m.json`
- `docs/reports/frontend_runtime_payload_provider_info_paid_6m.json`

Pass means:

- production gate, readiness, simulator reference parity, and frontend/provider contract all passed against the paid runtime path

## Minimal Subsets

### Base frontend/operator subset

Run:

- `FE-1`

Use when:

- you only need operator/browser confidence

### Low-fidelity runtime subset

Run:

- `FE-1`
- `FE-2`
- `RS-1`

Use when:

- you want confidence in the frontend plus RadarSimPy trial path

### High-fidelity contract subset

Run:

- `HF-1`
- `HF-2`

Use when:

- you changed scene backends or ray-tracing-adjacent logic

### Release-candidate subset

Run:

- `FE-1`
- `FE-2`
- `RS-1`
- `HF-2`
- `RS-2`

Add `HF-1` when the Sionna-style path is part of the candidate release story.

The one-command runner above executes this subset by default, with `HF-1` optional via `--with-sionna`.

## Current Gap

The main remaining gap is no longer scenario definition or runner wiring. It is release freeze:

- keep the release-candidate subset green as the default closure path
- decide whether `HF-1` is required in the default release story or remains optional
- cut a release-candidate snapshot from the refreshed stable reports
