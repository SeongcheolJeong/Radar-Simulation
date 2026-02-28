# Web E2E Graph Audit Quick Telemetry Strict-Mode Adoption Readiness Gate (M17.58)

## Goal

Add a readiness gate that helps decide whether strict mode can become the operational default.

1. track strict-import adoption signals (attempt/success, legacy-wrap usage, strict legacy-blocks)
2. expose a default-switch checklist summary (`READY` vs `HOLD`)
3. provide gate reset control for fresh rollout measurement windows

Implementation:

- strict adoption signal + checklist + UI controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- signal config/state:
  - `QUICK_TELEMETRY_STRICT_ADOPTION_MIN_SUCCESS_COUNT`
  - `quickTelemetryDrilldownStrictAdoptionSignals`
  - `quickTelemetryDrilldownStrictAdoptionGateStatus`
- signal updates:
  - `bumpQuickTelemetryDrilldownStrictAdoptionSignals`
  - `resetQuickTelemetryDrilldownStrictAdoptionSignals`
  - import/wrap actions update signal counters
- checklist derivation:
  - `quickTelemetryDrilldownStrictAdoptionChecklist`
  - `quickTelemetryDrilldownStrictAdoptionChecklistHint`
  - `quickTelemetryDrilldownStrictAdoptionChecklistPreview`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_adoption_gate_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_adoption_gate_preview`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_adoption_gate_reset`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_adoption_gate_status`

## Validation

Strict-adoption gate token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_adoption_gate.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. signal/checklist/reset tokens exist in panel source
2. strict import/wrap actions are wired to adoption signal updates
3. API regression suite remains pass
