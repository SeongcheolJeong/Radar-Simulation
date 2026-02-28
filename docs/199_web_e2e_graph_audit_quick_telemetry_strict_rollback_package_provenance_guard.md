# Web E2E Graph Audit Quick Telemetry Strict-Rollback Package Provenance Guard (M17.64)

## Goal

Add rollback-package provenance guard with source stamp and checksum hint before replay.

1. include provenance payload (`source_stamp`, `payload_checksum`, `checksum_hint`) in package exports
2. parse/import provenance and surface guard hint (`ok` vs `issue detected`)
3. treat provenance issue as replay guard condition requiring explicit confirmation

Implementation:

- strict-rollback package provenance guard:
  - `/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/panels.mjs`

## Behavior Contract

- provenance constants/helpers:
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_SOURCE_STAMP`
  - `QUICK_TELEMETRY_STRICT_ROLLBACK_DRILL_PACKAGE_CHECKSUM_ALGO`
  - `stableStringifyForChecksum`
  - `computeFnv1a32Hex`
  - `computeQuickTelemetryStrictRollbackDrillPackageChecksum`
  - `normalizeQuickTelemetryStrictRollbackDrillPackageProvenance`
- replay guard state/hints:
  - `provenance_guard`
  - `quickTelemetryStrictRollbackPackageProvenanceGuard`
  - `quickTelemetryStrictRollbackPackageProvenanceHint`
- UI keys:
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_provenance_hint`
  - `co_filter_import_audit_quick_telemetry_profile_import_filter_bundle_rollback_package_delta_confirm`

## Validation

Provenance-guard token validation:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_quick_telemetry_strict_rollback_package_provenance_guard.py
```

Backend/API regression check:

```bash
PYTHONPATH=src .venv/bin/python /home/seongcheoljeong/workspace/myproject/scripts/validate_web_e2e_orchestrator_api.py
```

Pass criteria:

1. provenance constants/helper/guard tokens exist
2. provenance hint + replay guard UI tokens exist
3. API regression suite remains pass
