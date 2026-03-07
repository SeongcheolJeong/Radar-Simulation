# Radar Decision Brief

- generated_at_utc: 2026-03-07T19:07:36.376Z
- graph_id: radar_minimal_v1

## Decision Snapshot
```text
generated_at_utc: 2026-03-07T19:07:25.911Z
decision: UNKNOWN
recommendation: unknown
baseline_id: playwright_baseline
current_run_id: grun_20260307_190725_49b8959d
compare_run_id: grun_20260307_190723_57ce2494
compare_runner_status: ready
selected_preset_pair: low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt
selected_preset_pair_label: Low Fidelity: RadarSimPy + FFD -> High Fidelity: PO-SBR
selected_preset_pair_forecast: baseline_forecast: state:planned | modules:planned:1 | sim:radarsimpy_adc | license:none | target_forecast: state:planned | modules:planned:2 | sim:auto | license:none | planned_deltas: | - backend: radarsimpy_rt -> po_sbr_rt | - provider: avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths -> avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr | - simulation_mode: radarsimpy_adc -> auto | - required_modules: radarsimpy -> rtxpy,igl
compare_session_count: 7
compare_history_retention_policy: retain_8 | keep_latest=8 | preserve_scope=none | preserve_pinned=false | preserve_saved=false | retained_rows=7/7 | managed_pinned_pairs=2 | retained_pinned_pairs=2 | extra_pinned_rows=0 | managed_saved_pairs=3 | retained_saved_pairs=3 | extra_saved_rows=0
retention_group_hint: none
retention_pairs(latest/extra/dropped): Low Fidelity Saved | low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt | Legacy Fixture | Sionna -> Current | Legacy Fixture | PO-SBR -> Current / - / -
managed_history_pair_count: 3
pinned_quick_actions: Low Fidelity Saved | Legacy Fixture | PO-SBR -> Current
latest_compare_session: 2026-03-07T19:07:25.910Z | source=preset_pair | status=ready | pair=Low Fidelity Saved | pin=yes | phase=current | compare=grun_20260307_190723_57ce2494 | current=grun_20260307_190725_49b8959d | assessment=review
latest_replayable_pair: Low Fidelity Saved | pinned=true
selected_history_pair: Low Fidelity Saved
selected_history_pair_meta: pinned=true | custom_label=Low Fidelity Saved
selected_history_pair_retention: state=latest_window | managed=pinned=true,saved=true | rows(visible/latest/retained)=4/4/4 | retention_window: keep_latest=8 | policy=retain_8 | pair=Low Fidelity Saved
selected_history_artifact_expectation: source=observed_ready_pair | assessment=review | required=4/4/4 | artifact_delta=none | path_hashes=5
selected_history_pair_preview: baseline_forecast: state:planned | modules:planned:1 | sim:radarsimpy_adc | license:none | target_forecast: state:planned | sim:auto | license:none | planned_deltas: | - backend: radarsimpy_rt -> analytic_targets | - provider: avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths -> - | - simulation_mode: radarsimpy_adc -> auto | - required_modules: radarsimpy -> - | - target_mode: current_config -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
compare_history_transfer_compact: transfer:import | compat:legacy_compatible | none | selected_pair_retention=unchanged
compare_history_transfer: imported 1 history row(s) and 1 artifact expectation snapshot(s) from graph_lab_compare_history_legacy_camelcase.json | schema=legacy_pre_v2 | compatibility=legacy_compatible
compare_history_import_preview: none | selected_pair_retention=unchanged
current_track: backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
compare_track: backend=radarsimpy_rt | sim=radarsimpy.sim_radar | mux=tdm | ant=isotropic | license=set
current_runtime: state:ready | sim:auto | license:none
compare_runtime: state:ready | modules:1/1 | sim:adc | adc:runtime | license:env
compare_assessment: review
compare_flags: path_delta:+4 | rd_peak_shift:+0/+12/0.00 | ra_peak_shift:+0/+3/0.00
artifact_inspector_status_badges: layout:default | probe:default | live:expanded | history:expanded | reset:clean | audit:idle | continuity:empty | health:idle | operator:idle
artifact_inspector_layout_state: default | live=expanded | history=expanded | probes=default | reset_required=no
artifact_inspector_probe_state: default | rd_cursor=14/43 | rd_lock=off | ra_cursor=7/43 | ra_lock=off
artifact_inspector_last_action: seq=0 | idle
artifact_inspector_recent_actions: none
artifact_inspector_audit_state: idle | total=0 | retained=0/3 | trimmed=0
artifact_inspector_audit_capacity: retained_limit=3 | retained=0 | total=0 | headroom=3 | overflow=no
artifact_inspector_audit_window: retained_seqs=none | newest=0 | oldest=0 | lost_before=0 | coverage=empty
artifact_inspector_audit_continuity: empty | retained_span=none | missing_prefix=none | continuity=empty
artifact_inspector_audit_health: idle | trust=empty | recommendation=not_needed
artifact_inspector_audit_health_reason: no_history | source=idle
artifact_inspector_audit_next_action: none | trigger=idle
artifact_inspector_audit_operator_summary: idle -> none | because=no_history
artifact_inspector_audit_summary: total=0 | retained=0 | trimmed=0 | next_seq=1 | state=empty
artifact_inspector_audit_controls: clear=disabled | recommended=not_needed | apply=disabled | reason=idle
artifact_inspector_controls: collapse=enabled | expand=disabled | reset=disabled | next_action: collapse_if_you_need_focus
gate_failure_count: 0
path_count_delta(current-compare): +4
rd_peak_delta(range/doppler): +0/+12
ra_peak_delta(range/angle): +0/+3
```

## Runtime Compare
- selected_preset_pair: low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt
- selected_preset_pair_label: Low Fidelity: RadarSimPy + FFD -> High Fidelity: PO-SBR
- current_track: backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
- compare_track: backend=radarsimpy_rt | sim=radarsimpy.sim_radar | mux=tdm | ant=isotropic | license=set
- compare_runner_status: track_compare_runner=ready | mode=preset_pair | baseline_preset=low_fidelity_radarsimpy_ffd | target_preset=current_config | compare=grun_20260307_190723_57ce2494 | current=grun_20260307_190725_49b8959d
- compare_status: compare_mode=runner_preset_pair | baseline_preset=low_fidelity_radarsimpy_ffd | run=grun_20260307_190723_57ce2494 | status=completed
- latest_replayable_pair: Low Fidelity Saved | pinned=true
- selected_history_pair: Low Fidelity Saved
- selected_history_pair_meta: pinned=true | custom_label=Low Fidelity Saved
- selected_history_pair_retention: state=latest_window | managed=pinned=true,saved=true | rows(visible/latest/retained)=4/4/4 | retention_window: keep_latest=8 | policy=retain_8 | pair=Low Fidelity Saved
- selected_history_artifact_expectation: source=observed_ready_pair | assessment=review | required=4/4/4 | artifact_delta=none | path_hashes=5
- compare_history_retention_policy: retain_8 | keep_latest=8 | preserve_scope=none | preserve_pinned=false | preserve_saved=false | retained_rows=7/7 | managed_pinned_pairs=2 | retained_pinned_pairs=2 | extra_pinned_rows=0 | managed_saved_pairs=3 | retained_saved_pairs=3 | extra_saved_rows=0
- retention_group_hint: none
- retention_pairs(latest/extra/dropped): Low Fidelity Saved | low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt | Legacy Fixture | Sionna -> Current | Legacy Fixture | PO-SBR -> Current / - / -
- compare_history_transfer_compact: transfer:import | compat:legacy_compatible | none | selected_pair_retention=unchanged
- compare_history_import_preview: none | selected_pair_retention=unchanged
- managed_history_pair_count: 3
- pinned_quick_actions: Low Fidelity Saved | Legacy Fixture | PO-SBR -> Current

## Selected Pair Forecast
```text
selected_pair: Low Fidelity: RadarSimPy + FFD -> High Fidelity: PO-SBR
baseline_forecast: state:planned | modules:planned:1 | sim:radarsimpy_adc | license:none
target_forecast: state:planned | modules:planned:2 | sim:auto | license:none
planned_deltas:
- backend: radarsimpy_rt -> po_sbr_rt
- provider: avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths -> avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr
- simulation_mode: radarsimpy_adc -> auto
- required_modules: radarsimpy -> rtxpy,igl
```

## Pinned Pair Quick Actions
```text
pinned_quick_action_count: 2
- [1] Low Fidelity Saved | baseline=low_fidelity_radarsimpy_ffd | target=current_config
  badges: assessment:review | fp:delta:5/5 | source:observed
  preview: baseline_forecast: state:planned | modules:planned:1 | sim:radarsimpy_adc | license:none | target_forecast: state:planned | sim:auto | license:none | planned_deltas: | - backend: radarsimpy_rt -> analytic_targets | - provider: avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths -> - | - simulation_mode: radarsimpy_adc -> auto | - required_modules: radarsimpy -> - | - target_mode: current_config -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
  artifact_expectation: source=observed_ready_pair | assessment=review | required=4/4/4 | artifact_delta=none | path_hashes=5
  artifact_path_hashes: path_hashes=5 | path_list_json:cdb7dff3/155693c0 | adc_cube_npz:92bb15ab/abd2995c
- [2] Legacy Fixture | PO-SBR -> Current | baseline=high_fidelity_po_sbr_rt | target=current_config
  badges: assessment:review | fp:delta:2/2 | source:imported_legacy_fixture
  preview: baseline_forecast: state:planned | modules:planned:2 | sim:auto | license:none | target_forecast: state:planned | sim:auto | license:none | planned_deltas: | - backend: po_sbr_rt -> analytic_targets | - provider: avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr -> - | - required_modules: rtxpy,igl -> - | - target_mode: current_config -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
  artifact_expectation: source=imported_legacy_fixture | assessment=review | required=4/4/4 | artifact_delta=none | path_hashes=2
  artifact_path_hashes: path_hashes=2 | path_list_json:aa11aa11/bb22bb22 | radar_map_npz:cc33cc33/dd44dd44
```

## Compare Session History
```text
compare_history_retention_policy: retain_8 | keep_latest=8 | preserve_scope=none | preserve_pinned=false | preserve_saved=false | retained_rows=7/7 | managed_pinned_pairs=2 | retained_pinned_pairs=2 | extra_pinned_rows=0 | managed_saved_pairs=3 | retained_saved_pairs=3 | extra_saved_rows=0
retention_group_hint: none
retention_pairs(latest/extra/dropped): Low Fidelity Saved | low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt | Legacy Fixture | Sionna -> Current | Legacy Fixture | PO-SBR -> Current / - / -
retention_rows(visible/retained): 7/7
compare_history_transfer_compact: transfer:import | compat:legacy_compatible | none | selected_pair_retention=unchanged

selected_history_pair_retention: state=latest_window | managed=pinned=true,saved=true | rows(visible/latest/retained)=4/4/4
retention_window: keep_latest=8 | policy=retain_8 | pair=Low Fidelity Saved

[1] 2026-03-07T19:07:25.910Z | source=preset_pair | status=ready | pair=Low Fidelity Saved | pin=yes | phase=current | compare=grun_20260307_190723_57ce2494 | current=grun_20260307_190725_49b8959d | assessment=review
[2] 2026-03-07T19:07:25.331Z | source=preset_pair | status=ready | pair=Low Fidelity Saved | pin=yes | phase=current | compare=grun_20260307_190722_bf89d248 | current=grun_20260307_190724_bbc9fb4d | assessment=review
[3] 2026-03-07T19:07:23.727Z | source=pin_current | status=pinned | pair=low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt | compare=grun_20260307_190722_aa0d8f02
[4] 2026-03-07T19:07:20.339Z | source=preset_pair | status=ready | pair=Low Fidelity Saved | pin=yes | phase=current | compare=grun_20260307_190719_fc75426a | current=grun_20260307_190719_a0096182 | assessment=review
[5] 2026-03-07T19:07:18.727Z | source=pin_current | status=pinned | pair=Low Fidelity Saved | pin=yes | compare=grun_20260307_190717_13bb02d6
[6] 2026-03-07T13:10:45Z | source=fixture_legacy_camelcase | status=ready | pair=Legacy Fixture | Sionna -> Current | phase=import_fixture | compare=grun_fixture_legacy_sionna_compare | current=grun_fixture_legacy_sionna_current | assessment=aligned | note=legacy fixture without schemaVersion using camelCase fields
```

## Compare History Import Preview
```text
import_preview_source: -
schema_version: -
schema_compatibility: -
retention_policy(current/imported/effective): retain_8/-/-
retention_effect(available/retained/pinned_pairs/extra_pinned_rows): 0/0/0/0
retention_pairs(merged_latest/merged_extra/merged_dropped): - / - / -
history_merge(existing/imported/new/overlap/merged): 0/0/0/0/0
pair_meta(existing/imported/merged): 0/0/0
artifact_expectations(existing/imported/merged): 0/0/0
selected_replay_pair(import): -
selected_replay_pair_after_merge: unchanged
selected_replay_pair_retention_after_merge: unchanged
import_pair_labels: -
apply_note: choose Import History to stage a bundle before merge
```

## Selected History Pair Preview
```text
selected_pair: Low Fidelity Saved
baseline_forecast: state:planned | modules:planned:1 | sim:radarsimpy_adc | license:none
target_forecast: state:planned | sim:auto | license:none
planned_deltas:
- backend: radarsimpy_rt -> analytic_targets
- provider: avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths -> -
- simulation_mode: radarsimpy_adc -> auto
- required_modules: radarsimpy -> -
- target_mode: current_config -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
```

## Selected History Pair Artifact Expectation
```text
artifact_expectation_source: observed_ready_pair
pair_label: Low Fidelity: RadarSimPy + FFD -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
observed_at_utc: 2026-03-07T19:07:25.910Z
observed_assessment: review
required_artifacts(current/compare/total): 4/4/4
artifact_presence_delta: none
optional_artifact_delta: none
current_required_missing: none
compare_required_missing: none
artifact_path_fingerprint_algo: fnv1a32_path_text
artifact_path_fingerprints:
- path_list_json: current=path_list.json#cdb7dff3 compare=path_list.json#155693c0
- adc_cube_npz: current=adc_cube.npz#92bb15ab compare=adc_cube.npz#abd2995c
- radar_map_npz: current=radar_map.npz#627f14d6 compare=radar_map.npz#eb3aaf9b
- graph_run_summary_json: current=graph_run_summary.json#5bb1a08c compare=graph_run_summary.json#56b8d175
- lgit_customized_output_npz: current=lgit_customized_output.npz#8c88bb95 compare=lgit_customized_output.npz#ede95ae2
artifact_rows:
- path_list_json: required=true current=true compare=true
- adc_cube_npz: required=true current=true compare=true
- radar_map_npz: required=true current=true compare=true
- graph_run_summary_json: required=true current=true compare=true
- lgit_customized_output_npz: required=false current=true compare=true
```

### Current Runtime Diagnostics
```text
state: ready
backend: analytic_targets
provider: -
mode: -
simulation_used: -
adc_source: -
license_source: none
module_report:
- none
runtime_error: -
```

### Compare Runtime Diagnostics
```text
state: ready
backend: radarsimpy_rt
provider: avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths
mode: runtime_provider
simulation_used: true
adc_source: runtime_payload_adc_sctr
license_source: env
module_report:
- radarsimpy: ok @15.0.1
runtime_error: -
```

## Compare Assessment
```text
assessment: review
flags: path_delta:+4 | rd_peak_shift:+0/+12/0.00 | ra_peak_shift:+0/+3/0.00
shape_status(adc/rd/ra): match/match/match
shape(adc): 256x4x2x2 vs 256x4x2x2
shape(rd): 16x64 vs 16x64
shape(ra): 8x64 vs 8x64
adc_source(current/compare): -/runtime
path_count_delta(current-compare): +4
rd_peak_delta(range/doppler/rel_db): +0/+12/0.00
ra_peak_delta(range/angle/rel_db): +0/+3/0.00
required_artifacts(current/compare/total): 4/4/4
artifact_presence_delta: none
optional_artifact_delta: none
```

## Artifact Inspector State
```text
artifact_inspector_status_badges: layout:default | probe:default | live:expanded | history:expanded | reset:clean | audit:idle | continuity:empty | health:idle | operator:idle
artifact_inspector_layout_state: default | live=expanded | history=expanded | probes=default | reset_required=no
artifact_inspector_probe_state: default | rd_cursor=14/43 | rd_lock=off | ra_cursor=7/43 | ra_lock=off
artifact_inspector_last_action: seq=0 | idle
artifact_inspector_recent_actions: none
artifact_inspector_audit_state: idle | total=0 | retained=0/3 | trimmed=0
artifact_inspector_audit_capacity: retained_limit=3 | retained=0 | total=0 | headroom=3 | overflow=no
artifact_inspector_audit_window: retained_seqs=none | newest=0 | oldest=0 | lost_before=0 | coverage=empty
artifact_inspector_audit_continuity: empty | retained_span=none | missing_prefix=none | continuity=empty
artifact_inspector_audit_health: idle | trust=empty | recommendation=not_needed
artifact_inspector_audit_health_reason: no_history | source=idle
artifact_inspector_audit_next_action: none | trigger=idle
artifact_inspector_audit_operator_summary: idle -> none | because=no_history
artifact_inspector_audit_summary: total=0 | retained=0 | trimmed=0 | next_seq=1 | state=empty
artifact_inspector_audit_controls: clear=disabled | recommended=not_needed | apply=disabled | reason=idle
artifact_inspector_controls: collapse=enabled | expand=disabled | reset=disabled | next_action: collapse_if_you_need_focus
```

## Current Artifacts
- graph_run_summary_json: /tmp/graph_lab_playwright_e2e_3bbuxe76/store/graph_runs/grun_20260307_190725_49b8959d/graph_run_summary.json
- radar_map_npz: /tmp/graph_lab_playwright_e2e_3bbuxe76/store/graph_runs/grun_20260307_190725_49b8959d/output/radar_map.npz
- adc_cube_npz: /tmp/graph_lab_playwright_e2e_3bbuxe76/store/graph_runs/grun_20260307_190725_49b8959d/output/adc_cube.npz
- path_list_json: /tmp/graph_lab_playwright_e2e_3bbuxe76/store/graph_runs/grun_20260307_190725_49b8959d/output/path_list.json

## Compare Artifacts
- graph_run_summary_json: /tmp/graph_lab_playwright_e2e_3bbuxe76/store/graph_runs/grun_20260307_190723_57ce2494/graph_run_summary.json
- radar_map_npz: /tmp/graph_lab_playwright_e2e_3bbuxe76/store/graph_runs/grun_20260307_190723_57ce2494/output/radar_map.npz
- adc_cube_npz: /tmp/graph_lab_playwright_e2e_3bbuxe76/store/graph_runs/grun_20260307_190723_57ce2494/output/adc_cube.npz
- path_list_json: /tmp/graph_lab_playwright_e2e_3bbuxe76/store/graph_runs/grun_20260307_190723_57ce2494/output/path_list.json

## Gate Evidence
- none

## Regression Session
- session_id: dssn_1772910455276
- session_recommendation: hold_some_candidates
- export_id: rexp_20260307_190735_f9831b85
- export_package_json: /tmp/graph_lab_playwright_e2e_3bbuxe76/store/regression_exports/rexp_20260307_190735_f9831b85/regression_package.json