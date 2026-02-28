# Web E2E Graph Audit Quick Telemetry Strict-Mode Rollout Helper (M17.57)

## Goal

Provide migration safety when operators switch import mode to `strict`.

1. detect legacy bare-object payloads under strict mode
2. show auto-wrap preview that converts legacy payload into strict wrapped payload
3. provide one-click helper action and operator hints for strict rollout

Implementation:

- strict rollout helper logic + UI controls:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- helper parser bridge:
  - `buildQuickTelemetryDrilldownImportFilterBundleStrictWrapCandidate`
  - `quickTelemetryDrilldownImportFilterBundleStrictWrapCandidate`
  - `quickTelemetryDrilldownImportFilterBundleStrictWrapHint`
  - `quickTelemetryDrilldownImportFilterBundleStrictWrapPreview`
- helper action:
  - `wrapQuickTelemetryDrilldownImportFilterBundleLegacyPayload`
  - success status:
    - `legacy payload wrapped to strict bundle preview (kind/schema/filter_bundle)`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollout_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_wrap_legacy`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_wrap_legacy_preview`

## Validation

Rollout-helper token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_import_filter_bundle_rollout_helper.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. strict rollout helper tokens exist in Graph Lab panel source
2. strict wrapper parse guard + helper action are both present
3. API regression suite remains pass after frontend change
