# Radar Decision Brief

- generated_at_utc: 2026-03-07T13:36:58.087Z
- graph_id: radar_minimal_v1

## Decision Snapshot
```text
generated_at_utc: 2026-03-07T13:36:57.767Z
decision: ADOPT
recommendation: adopt_candidate
baseline_id: playwright_baseline
current_run_id: grun_20260307_133655_7b61c56d
compare_run_id: grun_20260307_133655_7b61c56d
compare_runner_status: running
selected_preset_pair: low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt
selected_preset_pair_label: Low Fidelity: RadarSimPy + FFD -> High Fidelity: PO-SBR
selected_preset_pair_forecast: baseline_forecast: state:planned | modules:planned:1 | sim:radarsimpy_adc | license:none | target_forecast: state:planned | modules:planned:2 | sim:auto | license:none | planned_deltas: | - backend: radarsimpy_rt -> po_sbr_rt | - provider: avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths -> avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr | - simulation_mode: radarsimpy_adc -> auto | - required_modules: radarsimpy -> rtxpy,igl
compare_session_count: 7
compare_history_retention_policy: retain_8 | keep_latest=8
managed_history_pair_count: 3
pinned_quick_actions: Low Fidelity Saved | Legacy Fixture | PO-SBR -> Current
latest_compare_session: 2026-03-07T13:36:57.648Z | source=preset_pair | status=ready | pair=Low Fidelity Saved | pin=yes | phase=current | compare=grun_20260307_133654_12780c99 | current=grun_20260307_133656_c79b6a14 | assessment=review
latest_replayable_pair: Low Fidelity Saved | pinned=true
selected_history_pair: Low Fidelity Saved
selected_history_pair_meta: pinned=true | custom_label=Low Fidelity Saved
selected_history_artifact_expectation: source=observed_ready_pair | assessment=review | required=4/4/4 | artifact_delta=none | path_hashes=5
selected_history_pair_preview: baseline_forecast: state:planned | modules:planned:1 | sim:radarsimpy_adc | license:none | target_forecast: state:planned | sim:auto | license:none | planned_deltas: | - backend: radarsimpy_rt -> analytic_targets | - provider: avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths -> - | - simulation_mode: radarsimpy_adc -> auto | - required_modules: radarsimpy -> - | - target_mode: current_config -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
compare_history_transfer: imported 1 history row(s) and 1 artifact expectation snapshot(s) from graph_lab_compare_history_legacy_camelcase.json | schema=legacy_pre_v2 | compatibility=legacy_compatible
compare_history_import_preview: none
current_track: backend=radarsimpy_rt | sim=radarsimpy.sim_radar | mux=tdm | ant=isotropic | license=set
compare_track: backend=radarsimpy_rt | sim=radarsimpy.sim_radar | mux=tdm | ant=isotropic | license=set
current_runtime: state:ready | modules:1/1 | sim:adc | adc:runtime | license:env
compare_runtime: state:ready | modules:1/1 | sim:adc | adc:runtime | license:env
compare_assessment: aligned
compare_flags: none
gate_failure_count: 0
path_count_delta(current-compare): +0
rd_peak_delta(range/doppler): +0/+0
ra_peak_delta(range/angle): +0/+0
```

## Runtime Compare
- selected_preset_pair: low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt
- selected_preset_pair_label: Low Fidelity: RadarSimPy + FFD -> High Fidelity: PO-SBR
- current_track: backend=radarsimpy_rt | sim=radarsimpy.sim_radar | mux=tdm | ant=isotropic | license=set
- compare_track: backend=radarsimpy_rt | sim=radarsimpy.sim_radar | mux=tdm | ant=isotropic | license=set
- compare_runner_status: track_compare_runner: mode=preset_pair | baseline_ready=grun_20260307_133655_7b61c56d | baseline_preset=low_fidelity_radarsimpy_ffd | target_preset=current_config | phase=current
- compare_status: compare_mode=runner_preset_pair | baseline_preset=low_fidelity_radarsimpy_ffd | run=grun_20260307_133655_7b61c56d | status=completed
- latest_replayable_pair: Low Fidelity Saved | pinned=true
- selected_history_pair: Low Fidelity Saved
- selected_history_pair_meta: pinned=true | custom_label=Low Fidelity Saved
- selected_history_artifact_expectation: source=observed_ready_pair | assessment=review | required=4/4/4 | artifact_delta=none | path_hashes=5
- compare_history_retention_policy: retain_8 | keep_latest=8
- compare_history_import_preview: none
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
  artifact_path_hashes: path_hashes=5 | path_list_json:ee631f2c/e105e484 | adc_cube_npz:074faf80/0097ba58
- [2] Legacy Fixture | PO-SBR -> Current | baseline=high_fidelity_po_sbr_rt | target=current_config
  badges: assessment:review | fp:delta:2/2 | source:imported_legacy_fixture
  preview: baseline_forecast: state:planned | modules:planned:2 | sim:auto | license:none | target_forecast: state:planned | sim:auto | license:none | planned_deltas: | - backend: po_sbr_rt -> analytic_targets | - provider: avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr -> - | - required_modules: rtxpy,igl -> - | - target_mode: current_config -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
  artifact_expectation: source=imported_legacy_fixture | assessment=review | required=4/4/4 | artifact_delta=none | path_hashes=2
  artifact_path_hashes: path_hashes=2 | path_list_json:aa11aa11/bb22bb22 | radar_map_npz:cc33cc33/dd44dd44
```

## Compare Session History
```text
compare_history_retention_policy: retain_8 | keep_latest=8

[1] 2026-03-07T13:36:57.648Z | source=preset_pair | status=ready | pair=Low Fidelity Saved | pin=yes | phase=current | compare=grun_20260307_133654_12780c99 | current=grun_20260307_133656_c79b6a14 | assessment=review
[2] 2026-03-07T13:36:57.290Z | source=preset_pair | status=ready | pair=Low Fidelity Saved | pin=yes | phase=current | compare=grun_20260307_133654_65a3f3f1 | current=grun_20260307_133655_802d36a0 | assessment=review
[3] 2026-03-07T13:36:56.285Z | source=pin_current | status=pinned | pair=low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt | compare=grun_20260307_133654_12780c99
[4] 2026-03-07T13:36:53.254Z | source=preset_pair | status=ready | pair=Low Fidelity Saved | pin=yes | phase=current | compare=grun_20260307_133652_5b280044 | current=grun_20260307_133652_5278a48d | assessment=review
[5] 2026-03-07T13:36:51.753Z | source=pin_current | status=pinned | pair=Low Fidelity Saved | pin=yes | compare=grun_20260307_133650_455e6d39
[6] 2026-03-07T13:10:45Z | source=fixture_legacy_camelcase | status=ready | pair=Legacy Fixture | Sionna -> Current | phase=import_fixture | compare=grun_fixture_legacy_sionna_compare | current=grun_fixture_legacy_sionna_current | assessment=aligned | note=legacy fixture without schemaVersion using camelCase fields
```

## Compare History Import Preview
```text
import_preview_source: -
schema_version: -
schema_compatibility: -
retention_policy(current/imported/effective): retain_8/-/-
history_merge(existing/imported/new/overlap/merged): 0/0/0/0/0
pair_meta(existing/imported/merged): 0/0/0
artifact_expectations(existing/imported/merged): 0/0/0
selected_replay_pair(import): -
selected_replay_pair_after_merge: unchanged
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
observed_at_utc: 2026-03-07T13:36:57.648Z
observed_assessment: review
required_artifacts(current/compare/total): 4/4/4
artifact_presence_delta: none
optional_artifact_delta: none
current_required_missing: none
compare_required_missing: none
artifact_path_fingerprint_algo: fnv1a32_path_text
artifact_path_fingerprints:
- path_list_json: current=path_list.json#ee631f2c compare=path_list.json#e105e484
- adc_cube_npz: current=adc_cube.npz#074faf80 compare=adc_cube.npz#0097ba58
- radar_map_npz: current=radar_map.npz#f2c8645f compare=radar_map.npz#6708a317
- graph_run_summary_json: current=graph_run_summary.json#9fceb579 compare=graph_run_summary.json#54b16e91
- lgit_customized_output_npz: current=lgit_customized_output.npz#7c0888a6 compare=lgit_customized_output.npz#fc0e84de
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
assessment: aligned
flags: none
shape_status(adc/rd/ra): match/match/match
shape(adc): 256x4x2x2 vs 256x4x2x2
shape(rd): 16x64 vs 16x64
shape(ra): 8x64 vs 8x64
adc_source(current/compare): runtime/runtime
path_count_delta(current-compare): +0
rd_peak_delta(range/doppler/rel_db): +0/+0/0.00
ra_peak_delta(range/angle/rel_db): +0/+0/0.00
required_artifacts(current/compare/total): 4/4/4
artifact_presence_delta: none
optional_artifact_delta: none
```

## Current Artifacts
- graph_run_summary_json: /tmp/graph_lab_playwright_e2e_f8jeu9_4/store/graph_runs/grun_20260307_133655_7b61c56d/graph_run_summary.json
- radar_map_npz: /tmp/graph_lab_playwright_e2e_f8jeu9_4/store/graph_runs/grun_20260307_133655_7b61c56d/output/radar_map.npz
- adc_cube_npz: /tmp/graph_lab_playwright_e2e_f8jeu9_4/store/graph_runs/grun_20260307_133655_7b61c56d/output/adc_cube.npz
- path_list_json: /tmp/graph_lab_playwright_e2e_f8jeu9_4/store/graph_runs/grun_20260307_133655_7b61c56d/output/path_list.json

## Compare Artifacts
- graph_run_summary_json: /tmp/graph_lab_playwright_e2e_f8jeu9_4/store/graph_runs/grun_20260307_133655_7b61c56d/graph_run_summary.json
- radar_map_npz: /tmp/graph_lab_playwright_e2e_f8jeu9_4/store/graph_runs/grun_20260307_133655_7b61c56d/output/radar_map.npz
- adc_cube_npz: /tmp/graph_lab_playwright_e2e_f8jeu9_4/store/graph_runs/grun_20260307_133655_7b61c56d/output/adc_cube.npz
- path_list_json: /tmp/graph_lab_playwright_e2e_f8jeu9_4/store/graph_runs/grun_20260307_133655_7b61c56d/output/path_list.json

## Gate Evidence
- none

## Regression Session
- session_id: dssn_1772890617840
- session_recommendation: adopt_all_candidates
- export_id: rexp_20260307_133657_288a85e4
- export_package_json: /tmp/graph_lab_playwright_e2e_f8jeu9_4/store/regression_exports/rexp_20260307_133657_288a85e4/regression_package.json