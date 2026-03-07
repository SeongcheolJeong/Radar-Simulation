# Radar Decision Brief

- generated_at_utc: 2026-03-07T13:02:03.341Z
- graph_id: radar_minimal_v1

## Decision Snapshot
```text
generated_at_utc: 2026-03-07T13:02:03.014Z
decision: ADOPT
recommendation: adopt_candidate
baseline_id: playwright_baseline
current_run_id: grun_20260307_130201_37213d88
compare_run_id: grun_20260307_130200_d0e2ac85
compare_runner_status: ready
selected_preset_pair: low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt
selected_preset_pair_label: Low Fidelity: RadarSimPy + FFD -> High Fidelity: PO-SBR
selected_preset_pair_forecast: baseline_forecast: state:planned | modules:planned:1 | sim:radarsimpy_adc | license:none | target_forecast: state:planned | modules:planned:2 | sim:auto | license:none | planned_deltas: | - backend: radarsimpy_rt -> po_sbr_rt | - provider: avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths -> avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr | - simulation_mode: radarsimpy_adc -> auto | - required_modules: radarsimpy -> rtxpy,igl
compare_session_count: 4
managed_history_pair_count: 1
pinned_quick_actions: Low Fidelity Saved
latest_compare_session: 2026-03-07T13:02:03.014Z | source=preset_pair | status=ready | pair=Low Fidelity Saved | pin=yes | phase=current | compare=grun_20260307_130200_358b1e94 | current=grun_20260307_130201_37213d88 | assessment=review
latest_replayable_pair: Low Fidelity Saved | pinned=true
selected_history_pair: Low Fidelity Saved
selected_history_pair_meta: pinned=true | custom_label=Low Fidelity Saved
selected_history_artifact_expectation: source=observed_ready_pair | assessment=review | required=4/4/4 | artifact_delta=none | path_hashes=5
selected_history_pair_preview: baseline_forecast: state:planned | modules:planned:1 | sim:radarsimpy_adc | license:none | target_forecast: state:planned | sim:auto | license:none | planned_deltas: | - backend: radarsimpy_rt -> analytic_targets | - provider: avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths -> - | - simulation_mode: radarsimpy_adc -> auto | - required_modules: radarsimpy -> - | - target_mode: current_config -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
compare_history_transfer: compare history import preview cleared
import_preview: none
current_track: backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
compare_track: backend=radarsimpy_rt | sim=radarsimpy.sim_radar | mux=tdm | ant=isotropic | license=set
current_runtime: state:ready | sim:auto | license:none
compare_runtime: state:ready | modules:1/1 | sim:adc | adc:runtime | license:env
compare_assessment: review
compare_flags: path_delta:+4 | rd_peak_shift:+0/+12/0.00 | ra_peak_shift:+0/+3/0.00
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
- compare_runner_status: track_compare_runner=ready | mode=preset_pair | baseline_preset=low_fidelity_radarsimpy_ffd | target_preset=current_config | compare=grun_20260307_130200_358b1e94 | current=grun_20260307_130201_37213d88
- compare_status: compare_mode=runner_preset_pair | baseline_preset=low_fidelity_radarsimpy_ffd | run=grun_20260307_130200_d0e2ac85 | status=completed
- latest_replayable_pair: Low Fidelity Saved | pinned=true
- selected_history_pair: Low Fidelity Saved
- selected_history_pair_meta: pinned=true | custom_label=Low Fidelity Saved
- selected_history_artifact_expectation: source=observed_ready_pair | assessment=review | required=4/4/4 | artifact_delta=none | path_hashes=5
- managed_history_pair_count: 1
- pinned_quick_actions: Low Fidelity Saved

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
pinned_quick_action_count: 1
- [1] Low Fidelity Saved | baseline=low_fidelity_radarsimpy_ffd | target=current_config
  badges: assessment:review | fp:delta:5/5 | source:observed
  preview: baseline_forecast: state:planned | modules:planned:1 | sim:radarsimpy_adc | license:none | target_forecast: state:planned | sim:auto | license:none | planned_deltas: | - backend: radarsimpy_rt -> analytic_targets | - provider: avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths -> - | - simulation_mode: radarsimpy_adc -> auto | - required_modules: radarsimpy -> - | - target_mode: current_config -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
  artifact_expectation: source=observed_ready_pair | assessment=review | required=4/4/4 | artifact_delta=none | path_hashes=5
  artifact_path_hashes: path_hashes=5 | path_list_json:3f2eda29/f557cbd1 | adc_cube_npz:2ec04771/6baeb439
```

## Compare Session History
```text
[1] 2026-03-07T13:02:03.014Z | source=preset_pair | status=ready | pair=Low Fidelity Saved | pin=yes | phase=current | compare=grun_20260307_130200_358b1e94 | current=grun_20260307_130201_37213d88 | assessment=review
[2] 2026-03-07T13:02:02.153Z | source=pin_current | status=pinned | pair=low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt | compare=grun_20260307_130200_358b1e94
[3] 2026-03-07T13:01:59.280Z | source=preset_pair | status=ready | pair=Low Fidelity Saved | pin=yes | phase=current | compare=grun_20260307_130158_c592e59c | current=grun_20260307_130158_d49a4836 | assessment=review
[4] 2026-03-07T13:01:57.702Z | source=pin_current | status=pinned | pair=Low Fidelity Saved | pin=yes | compare=grun_20260307_130156_e40eab25
```

## Compare History Import Preview
```text
import_preview_source: -
schema_version: -
schema_compatibility: -
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
observed_at_utc: 2026-03-07T13:02:03.014Z
observed_assessment: review
required_artifacts(current/compare/total): 4/4/4
artifact_presence_delta: none
optional_artifact_delta: none
current_required_missing: none
compare_required_missing: none
artifact_path_fingerprint_algo: fnv1a32_path_text
artifact_path_fingerprints:
- path_list_json: current=path_list.json#3f2eda29 compare=path_list.json#f557cbd1
- adc_cube_npz: current=adc_cube.npz#2ec04771 compare=adc_cube.npz#6baeb439
- radar_map_npz: current=radar_map.npz#e368ef4c compare=radar_map.npz#1ddcda34
- graph_run_summary_json: current=graph_run_summary.json#ec8b4be6 compare=graph_run_summary.json#36342e8e
- lgit_customized_output_npz: current=lgit_customized_output.npz#5c8552bb compare=lgit_customized_output.npz#e1e4d7e3
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

## Current Artifacts
- graph_run_summary_json: /tmp/graph_lab_playwright_e2e_1pg7275p/store/graph_runs/grun_20260307_130201_37213d88/graph_run_summary.json
- radar_map_npz: /tmp/graph_lab_playwright_e2e_1pg7275p/store/graph_runs/grun_20260307_130201_37213d88/output/radar_map.npz
- adc_cube_npz: /tmp/graph_lab_playwright_e2e_1pg7275p/store/graph_runs/grun_20260307_130201_37213d88/output/adc_cube.npz
- path_list_json: /tmp/graph_lab_playwright_e2e_1pg7275p/store/graph_runs/grun_20260307_130201_37213d88/output/path_list.json

## Compare Artifacts
- graph_run_summary_json: /tmp/graph_lab_playwright_e2e_1pg7275p/store/graph_runs/grun_20260307_130200_d0e2ac85/graph_run_summary.json
- radar_map_npz: /tmp/graph_lab_playwright_e2e_1pg7275p/store/graph_runs/grun_20260307_130200_d0e2ac85/output/radar_map.npz
- adc_cube_npz: /tmp/graph_lab_playwright_e2e_1pg7275p/store/graph_runs/grun_20260307_130200_d0e2ac85/output/adc_cube.npz
- path_list_json: /tmp/graph_lab_playwright_e2e_1pg7275p/store/graph_runs/grun_20260307_130200_d0e2ac85/output/path_list.json

## Gate Evidence
- none

## Regression Session
- session_id: dssn_1772888523074
- session_recommendation: hold_some_candidates
- export_id: rexp_20260307_130203_6d7e9547
- export_package_json: /tmp/graph_lab_playwright_e2e_1pg7275p/store/regression_exports/rexp_20260307_130203_6d7e9547/regression_package.json