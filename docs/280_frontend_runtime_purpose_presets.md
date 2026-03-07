# Frontend Runtime Purpose Presets

## Purpose

Expose two practical implementation tracks in the frontend so operators can choose by purpose instead of manually rebuilding backend/runtime fields every time:

- low-fidelity path: `RadarSimPy + FFD`
- high-fidelity path: `ray-tracing backend`

## Presets

The runtime panel now exposes three preset buttons:

- `Low Fidelity: RadarSimPy + FFD`
  - backend: `radarsimpy_rt`
  - runtime provider: `avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths`
  - required modules: `radarsimpy`
  - simulation mode: `radarsimpy_adc`
  - device hint: `cpu`
- `High Fidelity: Sionna-style RT`
  - backend: `sionna_rt`
  - runtime provider: `avxsim.runtime_providers.mitsuba_rt_provider:generate_sionna_like_paths_from_mitsuba`
  - required modules: `mitsuba,drjit`
  - simulation mode: `auto`
  - device hint: `gpu`
  - advanced sample: fills `ego_origin_m`, `chirp_interval_s`, `min_range_m`, and a non-empty `spheres` JSON array
- `High Fidelity: PO-SBR`
  - backend: `po_sbr_rt`
  - runtime provider: `avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr`
  - required modules: `rtxpy,igl`
  - simulation mode: `auto`
  - device hint: `gpu`
  - advanced sample: fills repo/geometry defaults plus `bounces`, `rays_per_lambda`, angle defaults, and optional `components` JSON

## FFD Inputs

The runtime panel now accepts:

- `TX FFD Files (comma/newline)`
- `RX FFD Files (comma/newline)`

These are emitted into `scene_overrides.backend.tx_ffd_files` and `scene_overrides.backend.rx_ffd_files`.

## Advanced Controls

The runtime panel now exposes provider-specific advanced sections when the selected backend/provider matches:

- `Sionna-style RT Advanced`
  - `Mitsuba Ego Origin`
  - `Mitsuba Chirp Interval`
  - `Mitsuba Min Range`
  - `Mitsuba Spheres JSON`
- `PO-SBR Advanced`
  - `PO-SBR Repo Root`
  - `PO-SBR Geometry Path`
  - chirp/bounce/rays and angle controls
  - `PO-SBR Components JSON`

The purpose preset buttons also load sample values for these sections so a user does not start from an invalid empty runtime payload.

## Runtime Diagnostics

The runtime panel now exposes a `Runtime Diagnostics` surface with:

- availability badges such as `state:*`, `modules:*`, `sim:*`, `adc:*`, `license:*`
- a compact multiline summary showing:
  - backend/provider
  - runtime mode
  - module report
  - license source
  - simulation usage / ADC source
  - runtime error when present

This is fed from the actual `graph_run_summary` metadata when a run exists, and falls back to planned runtime configuration when the user has not run yet.

## Compare Workflow

The Decision Pane now exposes a lightweight operator workflow for low-vs-high track comparison:

- `Use Current as Compare`
  - locks the current run as the compare reference
  - keeps that reference pinned while the operator switches runtime presets and runs again
- `Run Preset Pair Compare`
  - executes any selected `baseline_preset -> target_preset` pair
  - default is `low_fidelity_radarsimpy_ffd -> current_config`
  - when `target_preset` is not `current_config`, the frontend also applies that preset into the runtime panel so the visible controls match the executed target run
- quick pair shortcuts
  - `Low -> Current`
  - `Low -> Sionna`
  - `Low -> PO-SBR`
  - these only change the selected preset pair; they do not run until `Run Preset Pair Compare` is clicked
- `Run Low -> Current Compare`
  - executes a low-fidelity `radarsimpy_rt` baseline first
  - then runs the current frontend track and pins the low-fidelity result as compare input
  - this is now a convenience wrapper over the generic preset-pair runner
  - reports `blocked` when the low-fidelity runtime is unavailable, instead of leaving the UI in an ambiguous state
- `Track Compare Workflow`
  - shows current/compare track labels
  - keeps the recommended sequence visible inside the UI

Practical flow:

1. Run the first track.
2. Click `Use Current as Compare`.
3. Switch to the other runtime preset.
4. Run again.
5. Inspect `Artifact Inspector` diff and use `Policy Gate` / `Run Session`.

Fast path:

1. Configure the target high-fidelity track.
2. Click `Run Preset Pair Compare` and keep `baseline_preset=low_fidelity_radarsimpy_ffd`.
3. Set `target_preset=current_config` to use the current runtime panel as-is, or select a concrete preset to force the target track.
4. If the low-fidelity runtime is installed, inspect the generated compare pair immediately.
5. If the UI reports `track_compare_runner_blocked`, install or expose the `radarsimpy` runtime first.

Shortcut:

1. Configure the target high-fidelity track manually.
2. Click `Run Low -> Current Compare`.
3. If the low-fidelity runtime is installed, inspect the generated compare pair immediately.
4. If the UI reports `track_compare_runner_blocked`, install or expose the `radarsimpy` runtime first.

The Decision Pane also keeps a dedicated `track_compare_status` line so compare-runner state is preserved even after later `Policy Gate`, `Run Session`, or `Export Session` actions update the general decision status.

The preset-pair section also keeps a `selected_pair` summary so the operator can see which two tracks will run before pressing the compare button.

It now also shows a `selected pair forecast` block with:

- `baseline_forecast`
- `target_forecast`

These are planned runtime diagnostics derived from the selected preset ids and current runtime panel state, so the operator can see whether a pair is likely to be `planned`, `ready`, or blocked by missing modules before running it.

The Decision Pane also keeps a `Compare Session History` block that records the latest manual compare actions and preset-pair runs, including:

- `source=manual_load`, `source=pin_current`, or `source=preset_pair`
- result status such as `loaded`, `pinned`, `ready`, `blocked`, or `failed`
- compare/current graph run ids when available
- compare assessment for completed preset-pair runs
- `latest_replayable_pair` so the operator can reuse the newest stored preset pair quickly

The history block also provides:

- `Use Latest History Pair`
  - restores the newest replayable `baseline_preset -> target_preset` into the selector controls
- `Run Latest History Pair`
  - immediately reruns that stored preset pair
  - if the stored target is `current_config`, the replay uses the current runtime panel state at replay time
- `selected_history_pair`
  - tracks the replayable pair currently chosen in the history dropdown
- `selected_history_pair_retention`
  - shows whether the currently selected replayable pair is inside the latest retention window or only surviving as an extra preserved row
  - also shows the selected pair's pinned/saved management flags and `rows(visible/latest/retained)`
- replayable pair selector badges
  - the history dropdown options now also show `KEEP:latest` or `KEEP:extra`
  - pinned pairs keep the existing `PIN | ...` prefix, so a preserved pinned row appears as `PIN | KEEP:latest | ...`
  - the selector itself is now grouped into `Latest Window` and `Extra Preserved` sections, so the retained-set structure is visible before selecting a pair
- `Use Selected History Pair`
  - restores the chosen replayable pair from history into the selector controls
- `Run Selected History Pair`
  - reruns the chosen replayable pair from history instead of always using the newest one

The compare-session history and the selected replayable pair now persist in browser `localStorage`, so a page refresh keeps the recent compare workflow intact on the same machine/browser profile.

It also supports lightweight pair management directly in the Decision Pane:

- `Save Selected Label`
  - saves a custom label for the currently selected replayable pair
- `Pin Selected History Pair`
  - pins the selected pair so it sorts to the top of the replayable pair selector
- `Delete Selected History Pair`
  - removes the selected pair and its matching history entries from the local compare-session store

Pinned pairs are also promoted into a top-level `Pinned Pair Quick Actions` block:

- `Use PIN: <label>`
  - restores that pinned replayable pair into the preset-pair compare selectors without opening the history dropdown
- `Run PIN: <label>`
  - reruns that pinned replayable pair directly from the top-level quick action area
- `pinned_quick_action_count`
  - summarizes how many pinned quick actions are currently promoted out of history
- `artifact_expectation:` / `artifact_path_hashes:`
  - each promoted pinned pair now shows the stored artifact expectation summary and compact path-fingerprint summary directly in the quick-action block
- quick badges
  - each promoted pinned pair now also shows color-coded status chips for `assessment`, artifact path-fingerprint delta state (`fp:match` / `fp:delta` / `fp:unseen`), and expectation `source`
- `Show PIN Details: <label>` / `Hide PIN Details: <label>`
  - expands the pinned card inline to show the preset-pair forecast (`baseline_forecast`, `target_forecast`, `planned_deltas`) and the full stored artifact expectation detail before running it

The same area now supports browser-to-browser transfer:

- `History Retention`
  - controls how many compare-session rows are kept in browser state
  - current policies:
    - `retain_2`, `retain_4`, `retain_8`
    - `retain_2_preserve_pinned`, `retain_4_preserve_pinned`, `retain_8_preserve_pinned`
    - `retain_2_preserve_saved`, `retain_4_preserve_saved`, `retain_8_preserve_saved`
  - `*_preserve_pinned` keeps the latest `N` rows and then keeps one newest retained row for each pinned replay pair, up to the in-app history cap
  - `*_preserve_saved` does the same for any replay pair that is either pinned or has a saved custom label
  - pruning still drops replay-pair metadata and artifact expectation snapshots that no longer have a retained history row
  - the summary line now shows `keep_latest`, `preserve_scope`, `preserve_pinned`, `preserve_saved`, retained-row counts, managed/retained pinned-vs-saved pair counts, and extra retained rows beyond the latest-`N` window
  - the detail preview now shows `retention_pairs(latest/extra/dropped)` so the operator can see which visible replay pairs are inside the latest window, kept as extra preserved rows, or absent from the retained set
- `Clear All History`
  - clears compare-session rows, replay-pair metadata, artifact expectation snapshots, and the current staged import preview
  - keeps the currently selected retention policy unchanged
- `Export History`
  - downloads a JSON bundle with the recent compare-session rows, selected replayable pair, pair metadata, and pair-scoped artifact expectation snapshots
  - now also includes the active `retention_policy`
  - the transfer hint now also shows the exported bundle schema version
- `Import History`
  - stages a previously exported JSON bundle as a dry-run import preview first
  - shows `import_preview`, merge counts, selected replay-pair availability, and imported pair labels before any local state changes
  - preview also shows `retention_policy(current/imported/effective)`
  - preview now also shows `retention_pairs(merged_latest/merged_extra/merged_dropped)` for the post-merge retained set
  - preview also shows `selected_replay_pair_retention_after_merge`, so the operator can see whether the imported selected pair would land in `latest_window`, `retained_extra`, `dropped`, or `missing`
  - requires `Apply Import Merge` to actually merge the previewed bundle into the current browser profile
  - `Clear Import Preview` discards the staged bundle without changing local history
  - restores replayable pairs that were deleted locally, as long as they exist in the imported bundle
  - restores any observed artifact expectation snapshot that was exported with the same replayable pair id
  - the transfer hint now shows `schema` and `compatibility` for the imported bundle
  - an additional warning badge appears when the imported bundle uses an unknown future schema and Graph Lab falls back to best-effort parsing
  - committed legacy fixtures are exercised in browser E2E for both no-schema snake_case and no-schema camelCase imports

Detailed schema and migration policy:

- [281_compare_history_bundle_schema_migration.md](/home/seongcheoljeong/workspace/myproject/docs/281_compare_history_bundle_schema_migration.md)

The Decision Summary and exported brief now include:

- `selected_history_pair_meta`
- `managed_history_pair_count`

The history area also renders a `Selected History Pair Preview` block before execution. It shows:

- `baseline_forecast`
- `target_forecast`
- `planned_deltas`

so the operator can inspect the expected backend/provider/module/license changes for the selected replayable pair before clicking `Run Selected History Pair`.

It now also renders a `Selected History Pair Artifact Expectation` block:

- `artifact_expectation_source: planned_default`
  - shown before a pair has been observed live
- `artifact_expectation_source: observed_ready_pair`
  - shown after a successful preset-pair run or after importing a bundle that already captured the snapshot
- `required_artifacts(current/compare/total)`
- `artifact_presence_delta`
- `optional_artifact_delta`
- `artifact_path_fingerprint_algo`
- `artifact_path_fingerprints`
  - captures a stable fingerprint of the observed artifact path text for `path_list_json`, `adc_cube_npz`, `radar_map_npz`, `graph_run_summary_json`, and optional LGIT output when present

The `Artifact Inspector` now also classifies the current-vs-compare pair into:

- `aligned`
- `review`
- `hold`

using concrete evidence from:

- ADC/RD/RA shape equality
- path-count delta
- top RD/RA peak-bin drift
- ADC source changes
- required/optional artifact presence deltas

It now also mirrors the currently selected history pair's artifact expectation snapshot directly inside the `Artifact Inspector`, including:

- `selected_history_artifact_expectation`
- `artifact_expectation_source`
- `artifact_path_fingerprint_algo`
- artifact path fingerprint rows for the stored current/compare artifact paths
- `Hide/Show Live Compare Evidence`
  - collapses or restores the current-vs-compare evidence block while keeping the assessment summary visible
- `Hide/Show History Snapshot`
  - collapses or restores the selected history pair snapshot while keeping the selected pair and summary line visible
- `Reset Layout`
  - restores both fold sections to their default expanded state and clears the probe cursor/peak-lock controls back to their default values

Those fold preferences now persist in browser `localStorage`, so a reload keeps the `Artifact Inspector` in the same collapsed/expanded state on the same machine/browser profile.

## Backend Behavior

Path-based backends now share the same antenna-aware FMCW synth path:

- `analytic_targets`
- `mesh_material_stub`
- `sionna_rt`
- `po_sbr_rt`
- `radarsimpy_rt`

When `tx_ffd_files/rx_ffd_files` are present, the synth path loads `FfdAntennaModel` and applies antenna gain during ADC construction.

## RadarSimPy Limitation

`radarsimpy_rt` can return a runtime ADC payload via `sim_radar`, but that payload does not currently ingest repo-side `.ffd` files directly.

Current rule:

- no FFD: use runtime ADC payload when available
- FFD enabled: use runtime/provider paths + repo synth with `FfdAntennaModel`

This keeps the low-fidelity RadarSimPy flow usable while still letting the operator inject measured antenna patterns.

## Local Runtime Bootstrap

The repo now auto-discovers a local RadarSimPy runtime for frontend/API workflows when available:

- package roots:
  - `RADARSIMPY_PACKAGE_ROOT`
  - bundled trial package under `external/radarsimpy_trial/...`
  - repo source tree under `external/radarsimpy/src`
- libcompat:
  - `RADARSIMPY_LIBCOMPAT_DIR`
  - bundled `external/radarsimpy_trial/libcompat/usr/lib/x86_64-linux-gnu`
- license:
  - existing `RADARSIMPY_LICENSE_FILE`
  - staged/import-time license under the runtime package
  - repo-local `external/radarsimpy/src/radarsimpy/license_RadarSimPy_*.lic`

This is what allows `Run Low -> Current Compare` and the default `Run Preset Pair Compare` flow to reach `ready` in the local workspace without manually exporting shell paths first.

## Decision Brief

`Export Brief` now includes a `Runtime Compare` section with:

- selected preset pair id/label
- current/compare track labels
- stored compare-runner status
- current runtime diagnostics block
- compare runtime diagnostics block

It also includes a `Compare Assessment` block with:

- compare assessment status
- compare flags
- shape/path/peak delta evidence
- ADC source delta
- required artifact coverage and artifact presence delta

`Export Brief` also includes a `Selected Pair Forecast` section so the chosen compare recipe and its planned runtime expectations are preserved outside the UI.

It now also exports a `Compare Session History` section so the operator can hand off recent compare actions and their outcomes without relying on the browser state.

The `Runtime Compare` summary inside the brief now also carries:

- `latest_replayable_pair`
- `selected_history_pair`
- `selected_history_pair_retention`
- `compare_history_import_preview`
  - a compact one-line import-preview summary near the top of the brief so staged import state is visible without scrolling down to the full preview section
  - now also carries `selected_pair_retention=<state>(visible/latest/retained)` so the selected imported replay pair's retention landing zone is visible even in the compact line

## Current Scope

This repo does not currently contain a direct `OptiX` or `HybridDynamicRT` runtime backend.

Today the practical high-fidelity choices exposed in the frontend are:

- `sionna_rt` through the repo's Mitsuba-based provider
- `po_sbr_rt` through the PO-SBR runtime provider
