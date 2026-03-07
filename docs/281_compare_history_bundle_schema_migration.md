# Compare History Bundle Schema Migration

## Scope

This note documents the Graph Lab compare-history export/import bundle used by:

- `Export History`
- `Import History`
- compare-history replay pair transfer across browser profiles

The current writer version in code is:

- `graph_lab_compare_history_export_v2`

Source of truth:

- [app.mjs](/home/seongcheoljeong/workspace/myproject/frontend/graph_lab/app.mjs)

## Current Export Schema

Graph Lab currently writes a JSON object with these top-level fields:

- `schema_version`
- `exported_at_utc`
- `retention_policy`
- `history`
- `pair_meta_by_id`
- `pair_artifact_expectation_by_id`
- `selected_replay_pair_id`

Field meaning:

- `history`
  - recent compare-session rows, normalized and capped to the in-app history limit
- `retention_policy`
  - active browser retention policy for compare-session history (`retain_2`, `retain_4`, `retain_8`)
- `pair_meta_by_id`
  - replayable pair metadata such as custom label and `pinned`
- `pair_artifact_expectation_by_id`
  - stored artifact expectation snapshots, including artifact-path fingerprint details
- `selected_replay_pair_id`
  - the replayable pair that should be re-selected after import

## Import Compatibility Rules

The import parser is intentionally permissive.

Accepted input patterns:

- exact current schema: `schema_version=graph_lab_compare_history_export_v2`
- legacy bundle with no `schema_version`
- snake_case or camelCase variants for top-level fields

Current normalization behavior:

- missing `schema_version` is normalized to `legacy_pre_v2`
- missing `retention_policy` leaves the current browser retention policy unchanged on import
- unknown extra fields are ignored
- malformed/non-object JSON is rejected
- history rows are normalized and truncated to the in-app history limit
- pair metadata and artifact expectation maps are normalized field-by-field

Current compatibility labels exposed in the UI:

- `exact`
  - bundle schema exactly matches the current writer version
- `legacy_compatible`
  - older/no-version bundle was accepted through normalization
- `forward_compatible_best_effort`
  - unknown future schema string was accepted on a best-effort basis because the required fields still parsed

Current UI signaling:

- `transfer:import`
- `schema:<value>`
- `compat:<value>`
- `warning:future-schema`
  - shown only when `compat=forward_compatible_best_effort`
- dry-run preview before merge
  - `Import History` stages the bundle and renders an `import_preview` summary before local history is changed
  - `Apply Import Merge` performs the actual merge
  - `Clear Import Preview` discards the staged import without changing persisted browser state

## Migration Policy

### Writer policy

- Graph Lab writes only the latest export schema
- current writer target: `graph_lab_compare_history_export_v2`

### Reader policy

- Graph Lab continues to accept older/no-version bundles when they can be normalized safely
- import is field-based, not strict-schema-only

### When to bump schema

Bump `schema_version` only when one of these happens:

- a top-level field is renamed or removed
- a required nested field changes meaning
- replay-pair metadata semantics change in a way old readers cannot infer
- artifact expectation snapshot semantics change beyond additive extension

Do not bump schema for purely additive optional fields when current import normalization can ignore missing values safely.

`retention_policy` remains in `v2` for this reason: it is additive and legacy bundles continue to import correctly without it.

## Recommended Upgrade Path

### `v1/no-version` to `v2`

No explicit offline migration step is required.

Recommended operator flow:

1. Import the legacy bundle in Graph Lab.
2. Verify the transfer hint shows `schema=legacy_pre_v2 | compatibility=legacy_compatible`.
3. Re-export once from the current UI.
4. Use the newly exported `v2` bundle as the canonical archive copy.

### Future `v3+`

If a future version needs a true schema break:

1. Add a dedicated normalization/migration function in `app.mjs`.
2. Preserve `v2` import support until all active archived bundles are rotated.
3. Keep the transfer hint explicit about both `schema` and `compatibility`.
4. Update this document and Playwright transfer checks in the same change.

## Validation Expectations

Any schema-related change should verify:

- export bundle `schema_version`
- import round-trip still restores:
  - replayable pairs
  - selected replay pair
  - retention policy when present
  - pair metadata
  - artifact expectation snapshots
- browser reload persistence is unaffected
- Playwright transfer coverage still passes

Current automated coverage:

- [validate_graph_lab_playwright_e2e.py](/home/seongcheoljeong/workspace/myproject/scripts/validate_graph_lab_playwright_e2e.py)
- fixture bundles:
  - [graph_lab_compare_history_legacy_no_schema.json](/home/seongcheoljeong/workspace/myproject/scripts/fixtures/graph_lab_compare_history_legacy_no_schema.json)
  - [graph_lab_compare_history_legacy_camelcase.json](/home/seongcheoljeong/workspace/myproject/scripts/fixtures/graph_lab_compare_history_legacy_camelcase.json)

## Practical Rule

If you are unsure whether a change needs a schema bump, default to:

- additive field: keep current schema
- semantic break: bump schema and add a migration path
