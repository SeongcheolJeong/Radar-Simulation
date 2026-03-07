# Radar Decision Brief

- generated_at_utc: 2026-03-07T11:38:15.397Z
- graph_id: radar_minimal_v1

## Decision Snapshot
```text
generated_at_utc: 2026-03-07T11:38:14.919Z
decision: ADOPT
recommendation: adopt_candidate
baseline_id: playwright_baseline
current_run_id: grun_20260307_113813_d097df0e
compare_run_id: grun_20260307_113813_d097df0e
compare_runner_status: running
selected_preset_pair: low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt
selected_preset_pair_label: Low Fidelity: RadarSimPy + FFD -> High Fidelity: PO-SBR
selected_preset_pair_forecast: baseline_forecast: state:planned | modules:planned:1 | sim:radarsimpy_adc | license:none | target_forecast: state:planned | modules:planned:2 | sim:auto | license:none | planned_deltas: | - backend: radarsimpy_rt -> po_sbr_rt | - provider: avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths -> avxsim.runtime_providers.po_sbr_rt_provider:generate_po_sbr_like_paths_from_posbr | - simulation_mode: radarsimpy_adc -> auto | - required_modules: radarsimpy -> rtxpy,igl
compare_session_count: 3
managed_history_pair_count: 1
pinned_quick_actions: Low Fidelity Saved
latest_compare_session: 2026-03-07T11:38:14.321Z | source=pin_current | status=pinned | pair=low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt | compare=grun_20260307_113812_55cdf496
latest_replayable_pair: low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt | pinned=false
selected_history_pair: Low Fidelity Saved
selected_history_pair_meta: pinned=true | custom_label=Low Fidelity Saved
selected_history_artifact_expectation: source=observed_ready_pair | assessment=review | required=4/4/4 | artifact_delta=none
selected_history_pair_preview: baseline_forecast: state:planned | modules:planned:1 | sim:radarsimpy_adc | license:none | target_forecast: state:planned | sim:auto | license:none | planned_deltas: | - backend: radarsimpy_rt -> analytic_targets | - provider: avxsim.runtime_providers.radarsimpy_rt_provider:generate_radarsimpy_like_paths -> - | - simulation_mode: radarsimpy_adc -> auto | - required_modules: radarsimpy -> - | - target_mode: current_config -> backend=analytic_targets | sim=auto | mux=tdm | ant=isotropic | license=none
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
- compare_runner_status: track_compare_runner: mode=preset_pair | baseline_ready=grun_20260307_113813_d097df0e | baseline_preset=low_fidelity_radarsimpy_ffd | target_preset=current_config | phase=current
- compare_status: compare_mode=runner_preset_pair | baseline_preset=low_fidelity_radarsimpy_ffd | run=grun_20260307_113813_d097df0e | status=completed
- latest_replayable_pair: low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt | pinned=false
- selected_history_pair: Low Fidelity Saved
- selected_history_pair_meta: pinned=true | custom_label=Low Fidelity Saved
- selected_history_artifact_expectation: source=observed_ready_pair | assessment=review | required=4/4/4 | artifact_delta=none
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
```

## Compare Session History
```text
[1] 2026-03-07T11:38:14.321Z | source=pin_current | status=pinned | pair=low_fidelity_radarsimpy_ffd -> high_fidelity_po_sbr_rt | compare=grun_20260307_113812_55cdf496
[2] 2026-03-07T11:38:13.165Z | source=preset_pair | status=ready | pair=Low Fidelity Saved | pin=yes | phase=current | compare=grun_20260307_113812_3f54d16e | current=grun_20260307_113812_55cdf496 | assessment=review
[3] 2026-03-07T11:38:11.690Z | source=pin_current | status=pinned | pair=Low Fidelity Saved | pin=yes | compare=grun_20260307_113810_fe05a791
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
observed_at_utc: 2026-03-07T11:38:13.165Z
observed_assessment: review
required_artifacts(current/compare/total): 4/4/4
artifact_presence_delta: none
optional_artifact_delta: none
current_required_missing: none
compare_required_missing: none
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
- graph_run_summary_json: /tmp/graph_lab_playwright_e2e__8pshbg_/store/graph_runs/grun_20260307_113813_d097df0e/graph_run_summary.json
- radar_map_npz: /tmp/graph_lab_playwright_e2e__8pshbg_/store/graph_runs/grun_20260307_113813_d097df0e/output/radar_map.npz
- adc_cube_npz: /tmp/graph_lab_playwright_e2e__8pshbg_/store/graph_runs/grun_20260307_113813_d097df0e/output/adc_cube.npz
- path_list_json: /tmp/graph_lab_playwright_e2e__8pshbg_/store/graph_runs/grun_20260307_113813_d097df0e/output/path_list.json

## Compare Artifacts
- graph_run_summary_json: /tmp/graph_lab_playwright_e2e__8pshbg_/store/graph_runs/grun_20260307_113813_d097df0e/graph_run_summary.json
- radar_map_npz: /tmp/graph_lab_playwright_e2e__8pshbg_/store/graph_runs/grun_20260307_113813_d097df0e/output/radar_map.npz
- adc_cube_npz: /tmp/graph_lab_playwright_e2e__8pshbg_/store/graph_runs/grun_20260307_113813_d097df0e/output/adc_cube.npz
- path_list_json: /tmp/graph_lab_playwright_e2e__8pshbg_/store/graph_runs/grun_20260307_113813_d097df0e/output/path_list.json

## Gate Evidence
- none

## Regression Session
- session_id: dssn_1772883495041
- session_recommendation: adopt_all_candidates
- export_id: rexp_20260307_113815_2cee3b1c
- export_package_json: /tmp/graph_lab_playwright_e2e__8pshbg_/store/regression_exports/rexp_20260307_113815_2cee3b1c/regression_package.json